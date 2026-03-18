import streamlit as st


def tab5():
    st.header("Crime Forecast For 90 Days")
    html = open("forecast_crime.html", "r").read()
    st.components.v1.html(html, height=800, scrolling=True)
