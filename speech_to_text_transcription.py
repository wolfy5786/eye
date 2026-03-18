import google.genai as genai
from google.genai import types 
from dotenv import load_dotenv
import os
import time # Needed for cleanup
from google.genai.errors import ServerError 
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Initialize client globally
client = genai.Client(api_key=API_KEY)

def extract_text(response):
    try:
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "Transcription failed: No content returned."
    except Exception as e:
        return f"Error extracting text: {e}"
    


@retry(
    wait=wait_exponential(min=4, max=30),     # Wait between 4s and 30s
    stop=stop_after_attempt(5),               # Total of 5 attempts
    retry=retry_if_exception_type(ServerError) 
)
def _generate_content_with_retry(contents):
    """Internal function to isolate the API call for retries on ServerError (503)."""
    print("  -> Executing API call (Attempt may be a retry)...")
    # You can safely use either 'gemini-2.5-flash' or 'gemini-2.5-pro' here
    return client.models.generate_content(
        model="gemini-2.5-flash", # Use Flash for speed
        contents=contents,
        config=types.GenerateContentConfig(temperature=0)
    )
    
def transcribe_911_call(filepath: str):
    """
    Transcribes an audio file by uploading it first and then using the File object.
    Uses the retryable function for reliable API interaction.
    """
    print(f"Attempting to upload file: {filepath}")
    
    # 1. Upload the file (happens once)
    audio_file = client.files.upload(file=filepath) 

    try:
        # 2. Define the content list
        text_part = types.Part(text="Transcribe this 911 emergency call accurately.")
        contents = [text_part, audio_file] 

        print(f"File uploaded (Name: {audio_file.name}, MIME: {audio_file.mime_type}). Calling generate_content with retry logic...")
        
        # 3. 🎯 FIX: CALL THE DECORATED RETRY FUNCTION
        response = _generate_content_with_retry(contents)
        
        print("Received successful response from Gemini.")
        return extract_text(response)
    
    except ServerError as e:
        # 4. Handle the final failure if all 5 retries exhausted
        print(f"❌ FATAL ERROR: API call failed after multiple retries. Server Error: {e}")
        return "Transcription failed due to persistent server overload (503)."

    finally:
        # 5. Clean up (Always executes)
        print(f"Cleaning up uploaded file: {audio_file.name}")
        client.files.delete(name=audio_file.name)        


incident_schema = {
    "type": "object",
    "properties": {
        "type_of_incident": {"type": "string", "description": "The specific type of crime or incident."},
        "location": {"type": "string", "description": "The street address or intersection where the incident is occurring."},
        "suspect_description": {"type": "string", "description": "Details about the suspect, e.g., clothing, height, hair color."},
        "vehicle_description": {"type": "string", "description": "Details about any vehicle involved, e.g., make, model, color, license plate."},
        "victim_description": {"type": "string", "description": "Description of the victim's state or appearance."},
        "urgency_level": {"type": "string", "description": "An assessment of the incident's urgency (e.g., High, Medium, Low)."}
    },
    "required": ["type_of_incident", "location", "suspect_description", "vehicle_description", "victim_description", "urgency_level"]
}


def extract_incident_entities(transcript: str):
    """Extracts structured entities from the transcript using Gemini's structured output."""
    prompt = f"""
    You are an emergency dispatcher assistant. Extract the incident details from the 911 call transcript based on the provided JSON schema.

    Transcript:
    {transcript}
    """
    
    # We will use the Flash model for speed here, as the task is purely data extraction.
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"text": prompt}],
        config=types.GenerateContentConfig( 
            response_mime_type="application/json",
            response_schema=incident_schema,
            temperature=0 
        )
    )
    
    # The output is a JSON string, so we must load it into a Python dictionary
    json_string = extract_text(response)
    
    try:
        # Use json.loads to convert the string output to a Python dictionary
        return json.loads(json_string)
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse JSON from model output. Raw output: {json_string}")
        return {"error": "JSON parsing failed", "raw_output": json_string}


transcript = transcribe_911_call("test.wav")
print("\nFinal Transcript:")
print(transcript)

# 2. Extract structured entities from the transcript
if not transcript.startswith("❌ FATAL ERROR"):
    incident_entities = extract_incident_entities(transcript)
    print("\nExtracted Incident Entities:")
    # Use json.dumps for pretty printing the dictionary
    print(json.dumps(incident_entities, indent=4))
else:
    print("\nSkipping entity extraction due to failed transcription.")