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
        type="password",
        key="gemini_api_key"
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

Return ONLY valid JSON.

{
    "Matched Rule": "string",
    "QE Classification": "QE or Not QE or Review",
    "Reason": "string"
}
"""

BULK_PROMPT = """
You are a payroll classification engine.

Return ONLY valid JSON.

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

        prompt = f"""
{SINGLE_PROMPT}

Description:
{description}
"""

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        text = response.text.strip()

        return json.loads(text)

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
            f"{i+1}. {d}"
            for i, d in enumerate(descriptions)
        )

        prompt = f"""
{BULK_PROMPT}

Descriptions:
{description_text}
"""

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        text = response.text.strip()

        results = json.loads(text)

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

# =====================================================
# QE LOOKUP
# =====================================================
st.subheader("QE Lookup")

search_text = st.text_input(
    "Payment Description",
    placeholder="Annual Leave, Casual Loading, Redundancy Payment, Overtime...",
    key="search_text"
)

if search_text:

    result = classify_payment(search_text)

    classification = result.get(
        "QE Classification",
        "Review"
    )

    if classification == "QE":

        st.success(
            f"✅ {result.get('Matched Rule', 'Unknown')} → QE"
        )

    elif classification == "Not QE":

        st.error(
            f"❌ {result.get('Matched Rule', 'Unknown')} → Not QE"
        )

    else:

        st.warning(
            f"⚠️ {result.get('Matched Rule', 'Unknown')} → Review"
        )

    st.caption(
        result.get("Reason", "")
    )

# =====================================================
# BULK UPLOAD
# =====================================================
st.divider()
st.subheader("📤 Bulk QE Classification")

template_df = pd.DataFrame({"Description": []})
template_output = BytesIO()
with pd.ExcelWriter(template_output, engine="openpyxl") as writer:
    template_df.to_excel(writer, sheet_name="Template", index=False)

st.download_button(
    "📄 Download Template",
    data=template_output.getvalue(),
    file_name="QE_Template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.file_uploader("Upload Completed Template", type=["xlsx"])

# =====================================================
# PROCESS FILE (WITH SUBMIT BUTTON AND STATE HANDLING)
# =====================================================
if uploaded_file:
    # IMPROVEMENT: Clear out historical results if a brand new file is detected
    if "current_file" not in st.session_state or st.session_state["current_file"] != uploaded_file.name:
        st.session_state["current_file"] = uploaded_file.name
        if "bulk_result" in st.session_state:
            del st.session_state["bulk_result"]

    input_df = pd.read_excel(uploaded_file, engine="openpyxl")
    input_df.columns = [str(col).strip() for col in input_df.columns]

    if "Description" not in input_df.columns:
        st.error("Excel file must contain a Description column.")
    else:
        submit_clicked = st.button("Process File", type="primary")
        
        if submit_clicked:
            try:
                with st.spinner("Classifying file..."):
                    processed_df = classify_bulk(input_df)
                    st.session_state["bulk_result"] = processed_df
                    st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Classification Error: {e}")

        if "bulk_result" in st.session_state:
            result_df = st.session_state["bulk_result"]

            # Safe filtering with fallback column structures if AI forgets a field
            if "QE Classification" not in result_df.columns:
                result_df["QE Classification"] = "Review"

            qe_df = result_df[result_df["QE Classification"] == "QE"]
            not_qe_df = result_df[result_df["QE Classification"] == "Not QE"]
            review_df = result_df[result_df["QE Classification"] == "Review"]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(result_df))
            col2.metric("QE", len(qe_df))
            col3.metric("Not QE", len(not_qe_df))
            col4.metric("Review", len(review_df))

            tab1, tab2, tab3 = st.tabs([
                f"✅ QE ({len(qe_df)})", 
                f"❌ Not QE ({len(not_qe_df)})", 
                f"⚠️ Review ({len(review_df)})"
            ])

            with tab1:
                st.dataframe(qe_df, use_container_width=True, hide_index=True)
            with tab2:
                st.dataframe(not_qe_df, use_container_width=True, hide_index=True)
            with tab3:
                st.dataframe(review_df, use_container_width=True, hide_index=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                result_df.to_excel(writer, sheet_name="Results", index=False)
                qe_df.to_excel(writer, sheet_name="QE", index=False)
                not_qe_df.to_excel(writer, sheet_name="Not QE", index=False)
                review_df.to_excel(writer, sheet_name="Review", index=False)

            st.download_button(
                "📥 Download Results",
                data=output.getvalue(),
                file_name="QE_Classification_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            if st.button("🧹 Clear Results"):
                if "bulk_result" in st.session_state:
                    del st.session_state["bulk_result"]
                st.rerun()
