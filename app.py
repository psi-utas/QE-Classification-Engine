import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import json

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="SuperQE",
    page_icon="🔍",
    layout="wide"
)

# =====================================================
# SIMPLE STYLING
# =====================================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.subheader("Gemini API")

    st.link_button(
        "Get Gemini API Key",
        "https://aistudio.google.com/u/1/api-keys",
        use_container_width=True
    )

    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    st.caption(
        "Your API key is used only for requests submitted during this session."
    )

if not gemini_api_key:
    st.info("Enter your Gemini API Key in the sidebar to continue.")
    st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================
genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-3.1-flash-lite"

model = genai.GenerativeModel(MODEL_NAME)

generation_config = {
    "temperature": 0,
    "top_p": 0.1,
    "top_k": 1,
    "response_mime_type": "application/json"
}

# =====================================================
# PROMPTS
# =====================================================
SINGLE_PROMPT = """
You are a payroll classification engine.

Return format JSON schema:
{
    "Matched Rule": "string",
    "QE Classification": "QE or Not QE or Review",
    "Reason": "string"
}
"""

BULK_PROMPT = """
You are a payroll classification engine.

Return format JSON schema:
[
  {
    "Description": "string",
    "QE Classification": "QE or Not QE or Review",
    "Matched Rule": "string",
    "Reason": "string"
  }
]
"""

# =====================================================
# CORE FUNCTIONS
# =====================================================
def classify_payment(description):

    try:

        prompt = f"{SINGLE_PROMPT}\n\nDescription:\n{description}"

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        return json.loads(response.text.strip())

    except Exception as e:

        return {
            "Matched Rule": "AI Error",
            "QE Classification": "Review",
            "Reason": str(e)
        }


def classify_bulk(input_df):

    try:

        descriptions = (
            input_df["Description"]
            .fillna("")
            .astype(str)
            .tolist()
        )

        description_text = "\n".join(
            [f"{i+1}. {d}" for i, d in enumerate(descriptions)]
        )

        prompt = f"{BULK_PROMPT}\n\nDescriptions:\n{description_text}"

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        results = json.loads(response.text.strip())

        return pd.DataFrame(results)

    except Exception as e:

        return pd.DataFrame({
            "Description": ["ERROR"],
            "QE Classification": ["Review"],
            "Matched Rule": ["AI Error"],
            "Reason": [str(e)]
        })

# =====================================================
# HEADER
# =====================================================
st.title("SuperQE")

st.caption(
    "ATO Payday Super 2026 Qualifying Earnings Classification Engine"
)

st.success(
    "🔒 No data stored. Files are processed in memory only and discarded immediately after results are returned."
)
import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import json

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="SuperQE",
    page_icon="🔍",
    layout="wide"
)

# =====================================================
# SIMPLE STYLING
# =====================================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.subheader("Gemini API")

    st.link_button(
        "Get Gemini API Key",
        "https://aistudio.google.com/u/1/api-keys",
        use_container_width=True
    )

    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    st.caption(
        "Your API key is used only for requests submitted during this session."
    )

if not gemini_api_key:
    st.info("Enter your Gemini API Key in the sidebar to continue.")
    st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================
genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-3.1-flash-lite"

model = genai.GenerativeModel(MODEL_NAME)

generation_config = {
    "temperature": 0,
    "top_p": 0.1,
    "top_k": 1,
    "response_mime_type": "application/json"
}

# =====================================================
# PROMPTS
# =====================================================
SINGLE_PROMPT = """
You are a payroll classification engine.

Return format JSON schema:
{
    "Matched Rule": "string",
    "QE Classification": "QE or Not QE or Review",
    "Reason": "string"
}
"""

BULK_PROMPT = """
You are a payroll classification engine.

Return format JSON schema:
[
  {
    "Description": "string",
    "QE Classification": "QE or Not QE or Review",
    "Matched Rule": "string",
    "Reason": "string"
  }
]
"""

# =====================================================
# CORE FUNCTIONS
# =====================================================
def classify_payment(description):

    try:

        prompt = f"{SINGLE_PROMPT}\n\nDescription:\n{description}"

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        return json.loads(response.text.strip())

    except Exception as e:

        return {
            "Matched Rule": "AI Error",
            "QE Classification": "Review",
            "Reason": str(e)
        }


def classify_bulk(input_df):

    try:

        descriptions = (
            input_df["Description"]
            .fillna("")
            .astype(str)
            .tolist()
        )

        description_text = "\n".join(
            [f"{i+1}. {d}" for i, d in enumerate(descriptions)]
        )

        prompt = f"{BULK_PROMPT}\n\nDescriptions:\n{description_text}"

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        results = json.loads(response.text.strip())

        return pd.DataFrame(results)

    except Exception as e:

        return pd.DataFrame({
            "Description": ["ERROR"],
            "QE Classification": ["Review"],
            "Matched Rule": ["AI Error"],
            "Reason": [str(e)]
        })

# =====================================================
# HEADER
# =====================================================
st.title("SuperQE")

st.caption(
    "ATO Payday Super 2026 Qualifying Earnings Classification Engine"
)

st.success(
    "🔒 No data stored. Files are processed in memory only and discarded immediately after results are returned."
)
