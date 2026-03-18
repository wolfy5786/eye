import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import MarkerCluster


import streamlit as st


def tab3():
    # ====================================================
    # 2. NYC & Long Island Farmers Markets Map
    # ====================================================
    st.header("Food Availability")

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

    st.markdown("---")
