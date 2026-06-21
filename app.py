import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import json

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# =====================================================
# GEMINI SETTINGS
# =====================================================

with st.sidebar:

    st.header("AI Settings")

    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

if not gemini_api_key:

    st.info(
        "Please enter your Gemini API Key in the sidebar."
    )

    st.stop()

genai.configure(
    api_key=gemini_api_key
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)
