import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from functions import generate_filter, run_query


def tab1(client, db):
    """
    Renders the UI for the Incident Map & Data tab.
    """

    # Initialize session state for incidents if it doesn't exist
    if "last_incidents" not in st.session_state:
        st.session_state.last_incidents = []

    user_input = st.text_input(
        "Search for incidents (e.g., 'vehicle thefts in Manhattan')"
    )

    # --- Data Fetching Block ---
    if st.button("Search Incidents"):
        with st.spinner("Querying database..."):
            try:
                # 1. Generate Filter
                query = generate_filter(user_input, client)
                collection = query.get("collection", "Incidents")
                filter_dict = query.get("filter", {})

                # 2. Run Query
                db_results = run_query(collection, filter_dict, db)

                # 3. Format Answer (optional, for a summary)
                # answer = format_answer(user_input, db_results, client)
                # st.session_state.last_answer = answer # You can use this in tab2

                # 4. Save results to state
                if isinstance(db_results, list) and len(db_results) > 0:
                    st.session_state.last_incidents = db_results
                else:
                    st.session_state.last_incidents = []
                    st.info("No incidents found matching your query.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.last_incidents = []

    # --- Display Block ---

    incidents_list = st.session_state.last_incidents

    if incidents_list:
        st.markdown("---")

        # ================================
        # MAP SECTION
        # ================================
        st.subheader(f"🗺️ Found {len(incidents_list)} Matching Incident(s) on Map")

        try:
            first_cam = incidents_list[0].get("matching_camera", {})
            first_loc = first_cam.get("camera_location", {})
            start_lat = first_loc.get("lat", 40.7128)
            start_lon = first_loc.get("lon", -74.0060)
        except IndexError:
            # Default to NYC coordinates if no incidents are found (shouldn't happen here, but good safeguard)
            start_lat, start_lon = 40.7128, -74.0060

        m = folium.Map(location=[start_lat, start_lon], zoom_start=12)

        for incident in incidents_list:
            cam = incident.get("matching_camera", {})
            loc = cam.get("camera_location", {})
            lat = loc.get("lat")
            lon = loc.get("lon")
            details = incident.get("incident_details", {})

            if lat is not None and lon is not None:
                popup_html = f"""
                <b>Incident:</b> {details.get("type_of_incident")}<br>
                <b>Suspect:</b> {details.get("suspect_description")}<br>
                <b>Camera:</b> {cam.get("camera_name")}
                """
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=details.get("type_of_incident"),
                    icon=folium.Icon(icon="exclamation-triangle", prefix="fa"),
                ).add_to(m)

        st_folium(m, height=500, use_container_width=True)

        # ================================
        # DATA TABLE SECTION with Expander for Details
        # ================================
        st.subheader("📝 Incident Details and Summary")

        # We will loop through incidents *again* to display a separate summary for each
        for i, incident in enumerate(incidents_list):
            details = incident.get("incident_details", {})
            cam = incident.get("matching_camera", {})

            # Use an expander for each incident for cleaner UI
            with st.expander(
                f"Incident {i + 1}: {details.get('type_of_incident', 'Unknown Type')} at {details.get('location_street', 'Unknown Location')}"
            ):
                # --- Incident Summary ---
                st.markdown("#### 📄 Basic Summary")
                st.markdown(f"**Report ID:** `{incident.get('report_id', 'N/A')}`")
                st.markdown(
                    f"**Timestamp:** **{incident.get('report_timestamp', 'N/A')}**"
                )

                st.markdown("---")

                # --- Incident Details Section ---
                st.markdown("#### 📍 Full Incident Details")

                detail_cols = st.columns(2)

                with detail_cols[0]:
                    st.markdown(f"**Type:** {details.get('type_of_incident', 'N/A')}")
                    st.markdown(
                        f"**Location (Street):** {details.get('location_street', 'N/A')}"
                    )
                    st.markdown(
                        f"**Location (Borough):** {details.get('location_borough', 'N/A')}"
                    )
                    st.markdown(
                        f"**Suspect Description:** {details.get('suspect_description', 'N/A')}"
                    )

        # --- Combined Data Table (Optional but kept for quick overview) ---
        st.markdown("---")
        st.markdown("### 📊 Quick Incident Overview Table")

        display_data = []
        for incident in incidents_list:
            details = incident.get("incident_details", {})
            cam = incident.get("matching_camera", {})

            display_data.append(
                {
                    "Timestamp": incident.get("report_timestamp"),
                    "Borough": details.get("location_borough"),
                    "Street": details.get("location_street"),
                    "Type": details.get("type_of_incident"),
                    "Suspect": details.get("suspect_description"),
                    "Camera": cam.get("camera_name"),
                    "Confidence": f"{cam.get('confidence')}%"
                    if cam.get("confidence") is not None
                    else "N/A",
                }
            )

        st.dataframe(pd.DataFrame(display_data))
