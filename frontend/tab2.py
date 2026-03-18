import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster  # HeatMap unused for now, but OK
from streamlit_folium import st_folium


# ====================================================
# 1. Crime Map Tab  — FIRST MAP INTEGRATED HERE
# ====================================================


def crime_map_tab():
    st.subheader("NYPD Crime Complaints (2024) – Marker Cluster")

    try:
        # --- Load data (same source as before) ---
        url_crime = "https://data.cityofnewyork.us/resource/qgea-i56i.csv"
        df = pd.read_csv(url_crime)

        # --------------------------------------------------------
        # 1. PREPARE THE DATA  (your first-map logic)
        # --------------------------------------------------------

        # Drop rows where latitude or longitude are missing
        df.dropna(subset=["latitude", "longitude"], inplace=True)

        # Convert date column to datetime objects
        df["cmplnt_fr_dt"] = pd.to_datetime(df["cmplnt_fr_dt"])

        # Extract the year into a new 'year' column
        df["year"] = df["cmplnt_fr_dt"].dt.year

        # --------------------------------------------------------
        # 2. FILTER BY YEAR
        # --------------------------------------------------------
        year_to_plot = 2024
        df_year = df[df["year"] == year_to_plot].copy()

        st.write(f"Plotting **{len(df_year)}** crimes for the year **{year_to_plot}**.")

        # --------------------------------------------------------
        # 3. CREATE THE FOLIUM MAP
        # --------------------------------------------------------

        # Coordinates for the center of NYC
        nyc_coords = [40.730610, -73.935242]

        # Create a base map
        crime_density_2024 = folium.Map(location=nyc_coords, zoom_start=11)

        # Using Marker Cluster
        marker_cluster = MarkerCluster().add_to(crime_density_2024)

        # Loop through your filtered data and add markers to the cluster
        for _, row in df_year.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=(
                    f"Crime: {row['ofns_desc']}<br>Date: {row['cmplnt_fr_dt'].date()}"
                ),
            ).add_to(marker_cluster)

        # --------------------------------------------------------
        # 4. DISPLAY THE MAP IN STREAMLIT
        # --------------------------------------------------------
        st_folium(crime_density_2024, height=500, width=900, key="crime_density_2024")

    except Exception as e:
        st.error(f"Error loading crime map: {e}")


# ====================================================
# 2. Farmers Markets Map Tab
# ====================================================


def farmers_markets_tab():
    st.subheader("Farmers Markets in NYC & Long Island")

    try:
        nys_market_url = "https://data.ny.gov/resource/qq4h-8p86.csv"
        df_nys_markets = pd.read_csv(nys_market_url)

        zip_col_name = "zip"  # adjust if schema changes
        zip_prefixes_to_include = [
            "100",
            "101",
            "102",
            "103",
            "104",  # NYC
            "110",
            "111",
            "112",
            "113",
            "114",
            "115",
            "116",
            "117",
            "118",
            "119",  # Long Island
        ]

        if zip_col_name in df_nys_markets.columns:
            df_nys_markets[zip_col_name] = df_nys_markets[zip_col_name].astype(str)
            df_filtered = df_nys_markets[
                df_nys_markets[zip_col_name].str.startswith(
                    tuple(zip_prefixes_to_include)
                )
            ].copy()
        else:
            st.warning(
                f"Zip code column '{zip_col_name}' not found in farmers market data."
            )
            df_filtered = pd.DataFrame(columns=df_nys_markets.columns)

        st.write(f"Total markets in NY State: **{len(df_nys_markets)}**")
        st.write(
            f"Markets in NYC & Long Island (by ZIP prefix): **{len(df_filtered)}**"
        )

        # Clean for mapping
        df_filtered.dropna(subset=["latitude", "longitude"], inplace=True)

        popup_cols = ["market_name", "address_line_1", "city", "market_link"]
        for col in popup_cols:
            if col in df_filtered.columns:
                df_filtered[col] = df_filtered[col].fillna("")

        # Build map
        map_coords = [40.75, -73.7]
        farmer_map = folium.Map(location=map_coords, zoom_start=10)
        marker_cluster = MarkerCluster().add_to(farmer_map)

        for _, row in df_filtered.iterrows():
            popup_html = f"""
            <b>{row["market_name"]}</b><br>
            {row["address_line_1"]}<br>
            {row["city"]}
            """

            if "market_link" in df_filtered.columns and row["market_link"]:
                popup_html += f'<br><a href="{row["market_link"]}" target="_blank">Visit Website</a>'

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=popup_html,
                tooltip=row["market_name"],
            ).add_to(marker_cluster)

        # Render in Streamlit
        st_folium(farmer_map, height=500, width=900, key="farmer_map")
    except Exception as e:
        st.error(f"Error loading farmers market map: {e}")


# ====================================================
# 3. Homeless Shelters Map Tab
# ====================================================


def homeless_shelters_tab():
    st.subheader("NYC Homeless Shelters")

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


# ====================================================
# 4. Main Tab 2 – wraps the three map tabs
# ====================================================


def tab2():
    st.header("Crime Density")
    html = open("crime_density_map.html", "r").read()

    st.components.v1.html(html, height=800, scrolling=True)
