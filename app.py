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
    st.info("Please enter your Gemini API Key in the sidebar.")
    st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================
genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-3.1-flash-lite"
model = genai.GenerativeModel(MODEL_NAME)

# IMPROVEMENT: Forced the model to strictly output valid JSON structures natively
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
Use ONLY ATO Payday Super 2026 Qualifying Earnings concepts and
[https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings](https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings)

Rules:
1. Use only ATO QE concepts.
2. Do not use external knowledge.
3. Do not guess.
4. If confidence is below 80%, return Review.
5. Keep reason under 10 words.
6. Return JSON only.
8. No long reasoning.

Return format JSON schema:
{
    "Matched Rule": "string",
    "QE Classification": "QE or Not QE or Review",
    "Reason": "string"
}
"""

BULK_PROMPT = """
You are a payroll classification engine.
Use ONLY ATO Payday Super 2026 Qualifying Earnings concepts and
[https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings](https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings)

Rules:
1. Use only ATO QE concepts.
2. Do not use external knowledge.
3. Do not guess.
4. If confidence is below 80%, return Review.
5. Keep reason under 10 words.
6. Return JSON only.
8. No long reasoning.

Return format JSON schema:
[
  {
    "Description": "string",
    "Matched Rule": "string",
    "QE Classification": "QE or Not QE or Review",
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
    descriptions = input_df["Description"].fillna("").astype(str).tolist()
    description_text = "\n".join([f"{i+1}. {d}" for i, d in enumerate(descriptions)])

    prompt = f"{BULK_PROMPT}\n\nDescriptions:\n{description_text}"
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    results = json.loads(response.text.strip())
    return pd.DataFrame(results)

# =====================================================
# HEADER & SINGLE SEARCH
# =====================================================
st.title("🔍 QE Lookup")

search_text = st.text_input(
    "",
    placeholder='Type payment description e.g. "Annual Leave", "Parental Leave Half Pay"...'
)

if search_text:
    result = classify_payment(search_text)
    classification = result.get("QE Classification", "Review")

    if classification == "QE":
        st.success(f"✅ {result.get('Matched Rule','Unknown')} → QE")
    elif classification == "Not QE":
        st.error(f"❌ {result.get('Matched Rule','Unknown')} → Not QE")
    else:
        st.warning(f"⚠️ {result.get('Matched Rule','Unknown')} → Review")

    st.caption(result.get("Reason", ""))

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
    input_df = pd.read_excel(uploaded_file, engine="openpyxl")
    input_df.columns = [str(col).strip() for col in input_df.columns]

    if "Description" not in input_df.columns:
        st.error("Excel file must contain a Description column.")
    else:
        # BUTTON ADDED HERE: Only run the heavy logic when explicitly triggered
        submit_clicked = st.button("🚀 SUBMIT TO AI", type="primary")
        
        # If the button is clicked, compute results and save to st.session_state
        if submit_clicked:
            try:
                with st.spinner("Classifying file..."):
                    processed_df = classify_bulk(input_df)
                    st.session_state["bulk_result"] = processed_df
                    st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Classification Error: {e}")

        # If results exist in the session state, render them seamlessly
        if "bulk_result" in st.session_state:
            result_df = st.session_state["bulk_result"]

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
            
            # Reset button to allow a new clean file run later if needed
            if st.button("🧹 Clear Results"):
                del st.session_state["bulk_result"]
                st.rerun()
