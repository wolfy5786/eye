import streamlit as st


def tab_cs():
    st.header("Crime Severity")
    html = open("type_of_crime_map.html", "r").read()

    st.components.v1.html(html, height=800, scrolling=True)
