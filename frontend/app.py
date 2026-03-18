import streamlit as st
from google.genai import Client
from mongodb_connector import db
from dotenv import load_dotenv
import os
from tab1 import tab1
from tab2 import tab2
from tab3 import tab3
from tab4 import tab4
from tab5 import tab5
from tab_cs import tab_cs

# --- App Configuration ---
st.set_page_config(layout="wide")
load_dotenv()

# Load the clients
gemini_client = Client(api_key=os.getenv("GEMINI_API_KEY"))
mongo_db = db

# --- Session State Initialization ---
# Initialize session state here in the main app
if "last_incidents" not in st.session_state:
    st.session_state.last_incidents = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""


# --- Streamlit UI Tabs ---
st.title("Sentinel AI")

tab_1, tab_2, tabcs, tab_3, tab_4, tab_5 = st.tabs(
    [
        "Chatbot for daily insights",
        "Crime Density",
        "Crime Severity",
        "Food Availability",
        "Homeless drop-in Centers",
        "Crime Forecast",
    ]
)

with tab_1:
    tab1(gemini_client, mongo_db)

with tab_2:
    tab2()

with tabcs:
    tab_cs()

with tab_3:
    tab3()

with tab_4:
    tab4()

with tab_5:
    tab5()
