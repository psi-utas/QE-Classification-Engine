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
# STYLING
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
        "Your API key is used only during this session."
    )

if not gemini_api_key:
    st.info("Enter your Gemini API Key to continue.")
    st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================
genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-2.5-flash"

model = genai.GenerativeModel(MODEL_NAME)

generation_config = {
    "temperature": 0,
    "top_p": 0.1,
    "top_k": 1,
    "response_mime_type": "application/json"
}

# =====================================================
# LOAD PROMPT
# =====================================================
try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        PROMPT = f.read()

except Exception as e:
    st.error(f"Unable to load prompt.txt: {e}")
    st.stop()

# =====================================================
# FUNCTIONS
# =====================================================
def classify_payment(description):

    try:

        prompt = f"""
{PROMPT}

Descriptions:
{json.dumps([description], ensure_ascii=False)}
"""

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        results = json.loads(response.text.strip())

        if isinstance(results, list) and len(results) > 0:
            return results[0]

        return {
            "Description": description,
            "QE Classification": "Review",
            "Reason": "No result returned"
        }

    except Exception as e:

        return {
            "Description": description,
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

        prompt = f"""
{PROMPT}

Descriptions:
{json.dumps(descriptions, ensure_ascii=False)}
"""

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        results = json.loads(
            response.text.strip()
        )

        if not isinstance(results, list):
            raise Exception(
                "Expected JSON array from Gemini."
            )

        result_df = pd.DataFrame(results)

        required_columns = [
            "Description",
            "QE Classification",
            "Reason"
        ]

        for col in required_columns:

            if col not in result_df.columns:
                result_df[col] = ""

        return result_df[required_columns]

    except Exception as e:

        return pd.DataFrame({
            "Description": ["ERROR"],
            "QE Classification": ["Review"],
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
    "🔒 No data stored. Files are processed in memory only."
)

# =====================================================
# SINGLE LOOKUP
# =====================================================
st.subheader("QE Lookup")

search_text = st.text_input(
    "Payment Description",
    placeholder="Annual Leave, Overtime, Salary..."
)

if search_text:

    result = classify_payment(search_text)

    classification = result.get(
        "QE Classification",
        "Review"
    )

    reason = result.get(
        "Reason",
        ""
    )

    if classification == "QE":
        st.success("✅ QE")

    elif classification == "Not QE":
        st.error("❌ Not QE")

    else:
        st.warning("⚠️ Review")

    st.caption(reason)

    st.dataframe(
        pd.DataFrame([result]),
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# BULK UPLOAD
# =====================================================
st.divider()

st.subheader("📤 Bulk QE Classification")

template_df = pd.DataFrame({
    "Description": []
})

template_output = BytesIO()

with pd.ExcelWriter(
    template_output,
    engine="openpyxl"
) as writer:

    template_df.to_excel(
        writer,
        sheet_name="Template",
        index=False
    )

st.download_button(
    "📄 Download Template",
    data=template_output.getvalue(),
    file_name="QE_Template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.file_uploader(
    "Upload Completed Template",
    type=["xlsx"]
)

# =====================================================
# PROCESS FILE
# =====================================================
if uploaded_file:

    if (
        "current_file" not in st.session_state
        or st.session_state["current_file"] != uploaded_file.name
    ):

        st.session_state["current_file"] = uploaded_file.name

        if "bulk_result" in st.session_state:
            del st.session_state["bulk_result"]

    input_df = pd.read_excel(
        uploaded_file,
        engine="openpyxl"
    )

    input_df.columns = [
        str(col).strip()
        for col in input_df.columns
    ]

    if "Description" not in input_df.columns:

        st.error(
            "Excel file must contain a Description column."
        )

    else:

        if st.button(
            "Process File",
            type="primary"
        ):

            with st.spinner(
                "Classifying file..."
            ):

                st.session_state["bulk_result"] = (
                    classify_bulk(input_df)
                )

            st.success(
                "Analysis complete!"
            )

        if "bulk_result" in st.session_state:

            result_df = st.session_state["bulk_result"]

            qe_df = result_df[
                result_df["QE Classification"] == "QE"
            ]

            not_qe_df = result_df[
                result_df["QE Classification"] == "Not QE"
            ]

            review_df = result_df[
                result_df["QE Classification"] == "Review"
            ]

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total",
                len(result_df)
            )

            col2.metric(
                "QE",
                len(qe_df)
            )

            col3.metric(
                "Not QE",
                len(not_qe_df)
            )

            col4.metric(
                "Review",
                len(review_df)
            )

            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True
            )

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                result_df.to_excel(
                    writer,
                    sheet_name="Results",
                    index=False
                )

            st.download_button(
                "📥 Download Results",
                data=output.getvalue(),
                file_name="QE_Classification_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            if st.button("🧹 Clear Results"):

                del st.session_state["bulk_result"]
                st.rerun()
