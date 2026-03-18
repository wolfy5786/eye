import os
import json
from google.genai import types
from google.genai.errors import ServerError 
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from speech_to_text_transcription import client, extract_text
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime


# Define simulated camera feeds
SIMULATED_CAMERAS = [
    {"name": "CAM-001 (Wall St & Hanover)", "file_path": "simulation_image_1.png", "lat": 40.7075, "lon": -74.0090},
    {"name": "CAM-002 (Broad St & Exchange)", "file_path": "simulation_image_2.png", "lat": 40.7081, "lon": -74.0110},
    {"name": "CAM-003 (Water St & Pearl)", "file_path": "simulation_image_3.png", "lat": 40.7060, "lon": -74.0085}
]


@retry(
    wait=wait_exponential(min=2, max=15), 
    stop=stop_after_attempt(3), 
    retry=retry_if_exception_type(ServerError) 
)
def find_matching_camera_from_images(cameras: list, suspect_description: str):
    """
    Analyzes a list of static images to find the one matching the suspect.
    """
    
    # 1. Build the prompt. Start with the main instruction.
    contents = [
        types.Part(text=f"""
        Analyze the following {len(cameras)} camera frames. 
        I am looking for a suspect described as: "{suspect_description}".

        Each image is labeled with its camera name. Review all of them and find the single camera frame that contains the strongest match for this suspect.
        """)
    ]

    # 2. Interleave images and their text labels
    for cam in cameras:
        image_path = cam['file_path']
        cam_name = cam['name']
        
        # Load image bytes from the local file
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Add the image part
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        # Add the text label for that image
        contents.append(types.Part(text=f"Image from: {cam_name}"))

    # 3. Add the final instruction (what to return)
    contents.append(types.Part(text="""
        Which camera frame contains the suspect?
        Return ONLY a JSON object with these exact keys:
        - winning_camera_name (The name of the camera with the best match)
        - justification (Explain *why* this frame is the best match, describing what you see.)
        - confidence_score (A number 1-100%)
    """))
    
    # 4. Call the API
    response = client.models.generate_content(
        model="gemini-2.5-pro", # Pro is best for reasoning across multiple images
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json")
    )
    
    # 5. Process and return the response
    json_string = extract_text(response)
    json_string = json_string.strip('```json').strip('```').strip()
    return json.loads(json_string)



def upload_report_to_s3(data_dict, bucket_name, object_key):
    """
    Converts a Python dictionary to a JSON string and uploads it to S3.
    
    Args:
        data_dict (dict): The final report data.
        bucket_name (str): The name of your S3 bucket (e.g., "my-911-sim-bucket").
        object_key (str): The desired filename in S3 (e.g., "reports/latest_incident.json").
    """
    print(f"\nUploading report to S3 bucket: {bucket_name}/{object_key}")
    
    # Convert the dictionary to a JSON string
    json_string = json.dumps(data_dict, indent=4)
    
    # Create an S3 client
    s3_client = boto3.client('s3')
    
    try:
        # Upload the JSON string
        s3_client.put_object(
            Body=json_string,
            Bucket=bucket_name,
            Key=object_key,
            ContentType='application/json'
        )
        print("✅ Report successfully uploaded to S3.")
        
    except FileNotFoundError:
        print("❌ The credentials file was not found.")
    except NoCredentialsError:
        print("❌ Credentials not available. Check your .env file or AWS config.")
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")

def upload_image_to_s3(local_file_path, bucket_name, object_key):
    """
    Uploads a local image file to S3 and makes it public.
    """
    s3_client = boto3.client('s3')
    
    try:
        # Use upload_file for files, it's more efficient
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            object_key,
            # This ExtraArgs is CRITICAL for your frontend
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/png'}
        )
        print(f"✅ Image successfully uploaded: {object_key}")
        
    except Exception as e:
        print(f"❌ Error uploading image {local_file_path}: {e}")


S3_BUCKET_NAME = "atharv-ruc-hackathon"
S3_OBJECT_KEY = "reports/latest_incident.json"


def main():
    # --- 1. INCIDENT REPORT (SIMULATED) ---
    print("--- 1. INCIDENT REPORT (SIMULATED) ---")
    
    # 🎯 FIX 1: Split location_text into street and borough
    incident_entities = {
        "type_of_incident": "Vehicle Theft",
        "location_street": "Wall Street",
        "location_borough": "Manhattan",
        "suspect_description": "Person wearing a black hoodie",
        "vehicle_description": "White Toyota Camry"
    }
    
    # ... (incident_location is fine) ...
    
    print(f"🎯 Target Suspect: {incident_entities['suspect_description']}")
    
    # --- 2. STATIC IMAGE ANALYSIS ---
    try:
        match_results = find_matching_camera_from_images(SIMULATED_CAMERAS, incident_entities['suspect_description'])
        print("\n--- 🎯 MATCHING CAMERA FOUND ---")
        print(json.dumps(match_results, indent=4))

        # --- 3. DATA CONSOLIDATION & IMAGE UPLOAD ---
        now = datetime.now()
        timestamp_filename_format = now.strftime("%Y-%m-%d-%H%M%S")
        timestamp_iso_format = now.isoformat()

        winning_cam_name = match_results.get('winning_camera_name')
        winning_cam_data = next((cam for cam in SIMULATED_CAMERAS if cam['name'] == winning_cam_name), {})
        
        # 🎯 FIX 2: Upload the winning image and get its public URL
        image_s3_url = None
        if winning_cam_data:
            local_image_path = winning_cam_data['file_path']
            image_s3_key = f"images/incident_{timestamp_filename_format}.png"
            
            # 1. Upload the image
            upload_image_to_s3(local_image_path, S3_BUCKET_NAME, image_s3_key)
            
            # 2. Construct the public URL
            
            image_s3_url = f"https://us-east-1.console.aws.amazon.com/s3/object/atharv-ruc-hackathon?region=us-east-1&prefix=images"

        # Build the final JSON report with all new fields
        final_report = {
            "report_id": f"incident_{timestamp_filename_format}",
            "report_timestamp": timestamp_iso_format,
            "incident_details": incident_entities,
            "matching_camera": {
                "camera_name": winning_cam_name,
                "camera_location": {
                    "lat": winning_cam_data.get('lat'),
                    "lon": winning_cam_data.get('lon')
                },
                # 🎯 ADDED THE PUBLIC URL
                "image_url": image_s3_url,
                "justification": match_results.get('justification'),
                "confidence": match_results.get('confidence_score')
            }
        }
        
        print("\n--- 📦 FINAL REPORT CONSOLIDATED ---")
        print(json.dumps(final_report, indent=4))

        # --- 4. UPLOAD THE JSON REPORT TO S3 ---
        report_s3_key = f"reports/incident_{timestamp_filename_format}.json"
        upload_report_to_s3(final_report, S3_BUCKET_NAME, report_s3_key)
            
    except Exception as e:
        print(f"❌ An error occurred during the pipeline: {e}")

if __name__ == "__main__":
    main()