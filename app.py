import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from io import BytesIO

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
# GEMINI SETUP
# =====================================================

model = None

if gemini_api_key:

    try:

        genai.configure(
            api_key=gemini_api_key
        )

        # Safer model for free tier
        model = genai.GenerativeModel(
            "gemini-1.5-flash"
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
# TEST BUTTON
# =====================================================

if model:

    if st.sidebar.button(
        "Test Gemini"
    ):

        try:

            response = model.generate_content(
                "Say hello"
            )

            st.sidebar.success(
                response.text
            )

        except Exception as e:

            st.sidebar.error(
                str(e)
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

    description = str(
        description
    ).strip()

    if description == "":

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review",
            "Reason": "Empty description"
        }

    prompt = f"""
You are an Australian payroll expert.

Using ATO Payday Super 2026 qualifying earnings principles.

Classify the payroll item below.

Return VALID JSON only.

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

        try:

            result = json.loads(
                content
            )

        except:

            return {
                "Matched Rule": "AI Response Error",
                "QE Classification": "Review",
                "Reason": content
            }

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
