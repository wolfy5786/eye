# import streamlit as st
# import json
# from google.genai import Client
# from mongodb_connector import db
# from dotenv import load_dotenv
# import os


# if "last_incident" not in st.session_state:
#     st.session_state.last_incident = None

# load_dotenv()

# client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# # --------------------------------------
# # Step 1: ask Gemini to convert message into a MongoDB filter
# # --------------------------------------


# def generate_filter(user_message):
#     prompt = (
#         """
#     Convert the user query into a MongoDB filter.

#     Respond ONLY with valid JSON.
#     Do NOT include backticks.
#     Do NOT include explanations.
#     Do NOT include natural language.
#     Do NOT include comments.
#     Do NOT include anything except pure JSON.

#     This is the MongoDB Schema:

#             final_report = {
#             "report_id",
#             "report_timestamp",
#             "incident_details",
#             "matching_camera": {
#                 "camera_name"
#                 "camera_location": {
#                     "lat"
#                     "lon"
#                 },
#                 "image_url",
#                 "justification",
#                 "confidence"
#             }
#         }


#     Required format EXACTLY:

#     {{

#         "collection": "Incidents",
#         "filter": {{}}
#     }}
#  """
#         + f"{user_message}"
#     )

#     response = client.models.generate_content(
#         model="gemini-2.0-flash", contents=prompt
#     ).text.strip()

#     # Safety: remove surrounding code fences if they appear
#     response = response.replace("```json", "").replace("```", "").strip()

#     # Debug print (optional)
#     # st.write("RAW GEMINI OUTPUT:", response)

#     return json.loads(response)


# # --------------------------------------
# # Step 2: execute the MongoDB query
# # --------------------------------------


# def run_query(collection, filter_dict):
#     try:
#         col = db[collection]
#         results = list(col.find(filter_dict, {"_id": 0}))
#         return results
#     except Exception as e:
#         return {"error": str(e)}


# # --------------------------------------
# # Step 3: ask Gemini to form a nice answer
# # --------------------------------------


# def format_answer(user_message, db_results):
#     prompt = f"""
#     User asked: {user_message}
#     DB results: {db_results}

#     Respond conversationally, summarizing the data clearly.
#     """

#     response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)

#     return response.text


import json

# --------------------------------------
# Step 1: ask Gemini to convert message into a MongoDB filter
# --------------------------------------


def generate_filter(user_message: str, client):
    """
    Asks Gemini to convert a user message into a MongoDB filter.
    """

    # 🎯 FIXED: Corrected the schema to be valid key: value pairs
    prompt = f"""
    Convert the user query into a MongoDB filter.

    Respond ONLY with valid JSON.
    Do NOT include backticks.
    Do NOT include explanations.
    Do NOT include natural language.
    Do NOT include comments.
    Do NOT include anything except pure JSON.

    This is the MongoDB Schema:
    {{
        "report_id": "string",
        "report_timestamp": "ISODate",
        "incident_details": {{
            "type_of_incident": "string",
            "location_street": "string",
            "location_borough": "string",
            "suspect_description": "string",
            "vehicle_description": "string",
            "victim_description": "string"
        }},
        "matching_camera": {{
            "camera_name": "string",
            "camera_location": {{
                "lat": "number",
                "lon": "number"
            }},
            "image_url": "string",
            "justification": "string",
            "confidence": "number"
        }}
    }}

    Required format EXACTLY:
    {{
        "collection": "Incidents",
        "filter": {{}}
    }}
    
    User Query: "{user_message}"
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    ).text.strip()

    # Safety: remove surrounding code fences if they appear
    response = response.replace("```json", "").replace("```", "").strip()
    return json.loads(response)


# --------------------------------------
# Step 2: execute the MongoDB query
# --------------------------------------


def run_query(collection: str, filter_dict: dict, db):
    """
    Executes a query on the specified MongoDB collection.
    """
    try:
        col = db[collection]
        # Find results and remove the internal _id for cleaner data
        results = list(col.find(filter_dict, {"_id": 0}))
        return results
    except Exception as e:
        return {"error": str(e)}


# --------------------------------------
# Step 3: ask Gemini to form a nice answer
# --------------------------------------


def format_answer(user_message: str, db_results: list, client):
    """
    Asks Gemini to summarize the database results into a natural answer.
    """
    prompt = f"""
    User asked: {user_message}
    Database query results: {db_results}

    Respond conversationally, summarizing the data clearly.
    If no results were found, just say "I'm sorry, I couldn't find any incidents matching that description."
    """

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text
