import folium
from streamlit_folium import st_folium
import pandas as pd


import streamlit as st


def tab4():
    # ====================================================
    # 3. NYC Homeless Shelters Map
    # ====================================================
    st.header("Homeless drop-in Centers")

    try:
        nys_homeless_url = "https://data.cityofnewyork.us/resource/bmxf-3rd4.csv"
        df_nys_homeless = pd.read_csv(nys_homeless_url)

        df_clean = df_nys_homeless.dropna(subset=["latitude", "longitude"])
        st.write(
            f"Original rows: **{len(df_nys_homeless)}**, "
            f"rows with coordinates: **{len(df_clean)}**"
        )

        shelter_map = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

        for _, row in df_clean.iterrows():
            lat = row["latitude"]
            lon = row["longitude"]

            popup_html = f"""
            <b>{row.get("center_name", "Unknown Center")}</b><br>
            Address: {row.get("address", "N/A")}<br>
            Borough: {row.get("borough", "N/A")}
            """

            iframe = folium.IFrame(popup_html, width=250, height=80)
            popup = folium.Popup(iframe)
            tooltip = row.get("center_name", "Shelter")

            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=tooltip,
                icon=folium.Icon(color="blue", icon="home"),
            ).add_to(shelter_map)

        st_folium(shelter_map, height=500, width=900, key="shelter_map")
    except Exception as e:
        st.error(f"Error loading homeless shelter map: {e}")
