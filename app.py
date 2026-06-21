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

if not gemini_api_key:

    st.info(
        "Please enter your Gemini API Key in the sidebar."
    )

    st.stop()

# =====================================================
# GEMINI CONFIGURATION
# =====================================================

genai.configure(
    api_key=gemini_api_key
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# =====================================================
# CLASSIFICATION FUNCTION
# =====================================================

def classify_payment(description):

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

Using ATO Payday Super 2026 Qualifying Earnings (QE) principles,
classify the payroll payment description below.

Return ONLY valid JSON.

{{
  "matched_rule":"",
  "classification":"QE|Not QE|Review",
  "reason":""
}}

Guidance:

QE Examples:
- Ordinary Time Earnings
- Annual Leave
- Sick Leave
- Personal Leave
- Family and Domestic Violence Leave
- Commissions
- Performance Bonus
- Casual Loading
- Shift Penalties

Not QE Examples:
- Overtime
- Parental Leave
- Maternity Leave
- Paternity Leave
- Jury Duty
- Government Paid Parental Leave
- Genuine Redundancy
- Employee Termination Payments

Review Examples:
- Car Allowance
- Phone Allowance
- Tool Allowance
- Meal Allowance

Payment Description:
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

        result = json.loads(content)

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
