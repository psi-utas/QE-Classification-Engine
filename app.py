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
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("AI Settings")

    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

# =====================================================
# GEMINI CONFIGURATION
# =====================================================

model = None

if gemini_api_key:

    try:

        genai.configure(
            api_key=gemini_api_key
        )

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        st.sidebar.success(
            "✅ Gemini Connected"
        )

    except Exception as e:

        st.sidebar.error(
            f"Gemini Error: {e}"
        )

else:

    st.sidebar.info(
        "Enter your Gemini API Key"
    )

# =====================================================
# DEBUG TEST
# =====================================================

if model:

    if st.sidebar.button(
        "Test Gemini"
    ):

        try:

            response = model.generate_content(
                "What is annual leave?"
            )

            st.sidebar.success(
                "Gemini Response Received"
            )

            st.write(response.text)

        except Exception as e:

            st.error(
                f"Test Error: {e}"
            )

# =====================================================
# CLASSIFICATION FUNCTION
# =====================================================

def classify_payment(description):

    if model is None:

        return {
            "Matched Rule": "No AI Model",
            "QE Classification": "Review",
            "Reason": "Gemini API key not configured"
        }

    if pd.isna(description):

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review",
            "Reason": "Empty description"
        }

    description = str(description).strip()

    if description == "":

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review",
            "Reason": "Empty description"
        }

    prompt = f"""
You are an Australian payroll and superannuation specialist.

Using ATO Payday Super 2026 Qualifying Earnings principles.

Classify the payment description.

Return ONLY valid JSON.

{{
  "matched_rule":"",
  "classification":"QE|Not QE|Review",
  "reason":""
}}

Description:
{description}
"""

    try:

        response = model.generate_content(
            prompt
        )

        content = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(
            content
        )

        return {
            "Matched Rule":
                result.get(
                    "matched_rule",
                    "No Match Found"
                ),
            "QE Classification":
                result.get(
                    "classification",
                    "Review"
                ),
            "Reason":
                result.get(
                    "reason",
                    ""
                )
        }

    except Exception as e:

        return {
            "Matched Rule": "AI Error",
            "QE Classification": "Review",
            "Reason": str(e)
        }
