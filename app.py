import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import json

# PAGE CONFIG
st.set_page_config(
    page_title="SuperQE",
    page_icon="🔵",
    layout="wide"
)

# SIDEBAR
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

# GEMINI CONFIG
genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-3.1-flash-lite"
model = genai.GenerativeModel(MODEL_NAME)

generation_config = {
    "temperature": 0,
    "top_p": 0.1,
    "top_k": 1,
    "response_mime_type": "application/json" 
}

# PROMPTS
SINGLE_PROMPT = """
You are a payroll classification engine.
Use ONLY ATO Payday Super 2026 Qualifying Earnings concepts and
[https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings](https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/what-payments-are-qualifying-earnings)

Rules:
1. Base your classification strictly on the provided ATO Payday Super 2026 Qualifying Earnings concepts.
2. Rely only on the clear facts directly mentioned in the context; do not assume or extrapolate.
3. If a description is ambiguous, missing context, or could be an expense allowance (e.g., tool/car/meal), classify it strictly as "Review".
4. If a payment description explicitly includes words like 'termination', 'unused leave on exit', 'redundancy', or 'paid out on resignation', classify it strictly as "Not QE".
5. Keep the "Reason" field highly concise and strictly under 10 words.
6. Populate the JSON schema keys exactly as requested without omitting fields or including markdown code blocks.

Guidance:

QE Examples:
- Ordinary hours of work (base wages, hourly wages, salary, or flat piece rates)
- Casual loading
- Shift penalties and public holiday penalties (even if worked as ordinary hours)
- Paid leave taken during employment (Annual leave, Sick leave, Personal leave, Carer's leave)
- Miscellaneous paid leave (Family and Domestic Violence leave, Study leave, Special paid leave, Gardening leave)
- Rostered Days Off (RDOs) or Time Off In Lieu (TOIL) taken and paid at ordinary rates
- Annual leave loading (unless it is explicitly linked to a lost opportunity to work overtime)
- Cashed out leave in service (Cashed out annual, long service, or sick leave while still employed)
- Long service leave (not paid under a portable scheme)
- Workers' compensation where the employee actually performs work or is required to attend work
- All employee commissions (including commissions for work performed entirely outside ordinary hours)
- Salary sacrifice superannuation contributions (pre-tax amounts that would have been OTE if paid as cash)
- Performance bonuses, Christmas bonuses, retention bonuses, sign-on bonuses, and referral bonuses
- Higher duties allowances, task allowances, skill allowances, qualification allowances, first-aid allowances, or danger allowances
- Payments in lieu of notice upon termination (this is an explicit exception to exit rules)
- Directors fees
- Charge rates or contract payments made to independent contractors paid wholly or principally for their labour

Not QE Examples:
- Overtime hours and any overtime loading or overtime penalties
- Cash out of TOIL (Time Off In Lieu) of overtime paid out in cash while in service
- Unused leave paid out on termination (Unused annual leave, unused long service leave, or unused sick leave paid out upon resignation/exit)
- Employer-paid parental leave (Maternity leave, Paternity leave, or Adoption leave)
- Government Paid Parental Leave (GPPL)
- Workers' compensation where the employee is NOT required to work (including top-ups or make-up pay)
- Ancillary leave (Jury duty leave, Community service leave, Emergency management leave, Defence reserve leave)
- Annual leave loading that is explicitly and clearly linked to a lost opportunity to work overtime
- Long service leave paid out under a portable long service leave scheme
- Genuine redundancy payments, severance pay, and Employee Termination Payments (ETPs)
- Bonuses earned solely for work performed entirely outside ordinary hours
- Salary sacrifice SUPERANNUATION contributions (Pre-tax amounts sacrificed specifically into a super fund)
- Overtime hours, overtime loading, and cash out of overtime TOIL
- Unused leave paid out on termination (Annual or Long service leave paid upon exit)
- Employer-paid or Government-paid parental leave
- Genuine redundancy payments, severance pay, and ETPs
- Salary sacrifice for NON-SUPER fringe benefits (e.g., Gym salary sacrifice, Novated car leases, Laptop/Device packaging)
- Bonuses earned solely for work performed entirely outside ordinary hours

Review Examples:
- Expense allowances (Expected to be fully spent by the employee in the course of doing their job)
- Reimbursements (Payments made to cover exact, receipted out-of-pocket business expenses)
- Uniform allowances or Laundry allowances
- Tool allowances or Equipment allowances
- Car allowances, Motor vehicle allowances, or Travel allowances (fixed or per-KM)
- Phone allowances, Internet allowances, or Home office allowances
- Meal allowances, Living Away From Home Allowances (LAFHA), or Accommodation allowances
- Underpayments, Back pay, or Lump Sum payments in arrears (requires reviewing what the original payment type was)

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
1. Base your classification strictly on the provided ATO Payday Super 2026 Qualifying Earnings concepts.
2. Rely only on the clear facts directly mentioned in the context; do not assume or extrapolate.
3. If a description is ambiguous, missing context, or could be an expense allowance (e.g., tool/car/meal), classify it strictly as "Review".
4. If a payment description explicitly includes words like 'termination', 'unused leave on exit', 'redundancy', or 'paid out on resignation', classify it strictly as "Not QE".
5. Keep the "Reason" field highly concise and strictly under 10 words.
6. Populate the JSON schema keys exactly as requested without omitting fields or including markdown code blocks.

Guidance:

QE Examples:
- Ordinary hours of work (base wages, hourly wages, salary, or flat piece rates)
- Casual loading
- Shift penalties and public holiday penalties (even if worked as ordinary hours)
- Paid leave taken during employment (Annual leave, Sick leave, Personal leave, Carer's leave)
- Miscellaneous paid leave (Family and Domestic Violence leave, Study leave, Special paid leave, Gardening leave)
- Rostered Days Off (RDOs) or Time Off In Lieu (TOIL) taken and paid at ordinary rates
- Annual leave loading (unless it is explicitly linked to a lost opportunity to work overtime)
- Cashed out leave in service (Cashed out annual, long service, or sick leave while still employed)
- Long service leave (not paid under a portable scheme)
- Workers' compensation where the employee actually performs work or is required to attend work
- All employee commissions (including commissions for work performed entirely outside ordinary hours)
- Salary sacrifice SUPERANNUATION contributions (Pre-tax amounts sacrificed specifically into a super fund)
- Performance bonuses, Christmas bonuses, retention bonuses, sign-on bonuses, and referral bonuses
- Higher duties allowances, task allowances, skill allowances, qualification allowances, first-aid allowances, or danger allowances
- Payments in lieu of notice upon termination (this is an explicit exception to exit rules)
- Directors fees
- Charge rates or contract payments made to independent contractors paid wholly or principally for their labour

Not QE Examples:
- Overtime hours and any overtime loading or overtime penalties
- Cash out of TOIL (Time Off In Lieu) of overtime paid out in cash while in service
- Unused leave paid out on termination (Unused annual leave, unused long service leave, or unused sick leave paid out upon resignation/exit)
- Employer-paid parental leave (Maternity leave, Paternity leave, or Adoption leave)
- Government Paid Parental Leave (GPPL)
- Workers' compensation where the employee is NOT required to work (including top-ups or make-up pay)
- Ancillary leave (Jury duty leave, Community service leave, Emergency management leave, Defence reserve leave)
- Annual leave loading that is explicitly and clearly linked to a lost opportunity to work overtime
- Long service leave paid out under a portable long service leave scheme
- Genuine redundancy payments, severance pay, and Employee Termination Payments (ETPs)
- Bonuses earned solely for work performed entirely outside ordinary hours
- Salary sacrificed amounts that relate to non-OTE payments (such as sacrificing overtime or parental leave)
- Overtime hours, overtime loading, and cash out of overtime TOIL
- Unused leave paid out on termination (Annual or Long service leave paid upon exit)
- Employer-paid or Government-paid parental leave
- Genuine redundancy payments, severance pay, and ETPs
- Salary sacrifice for NON-SUPER fringe benefits (e.g., Gym salary sacrifice, Novated car leases, Laptop/Device packaging)
- Bonuses earned solely for work performed entirely outside ordinary hours

Review Examples:
- Expense allowances (Expected to be fully spent by the employee in the course of doing their job)
- Reimbursements (Payments made to cover exact, receipted out-of-pocket business expenses)
- Uniform allowances or Laundry allowances
- Tool allowances or Equipment allowances
- Car allowances, Motor vehicle allowances, or Travel allowances (fixed or per-KM)
- Phone allowances, Internet allowances, or Home office allowances
- Meal allowances, Living Away From Home Allowances (LAFHA), or Accommodation allowances
- Underpayments, Back pay, or Lump Sum payments in arrears (requires reviewing what the original payment type was)

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

# CORE FUNCTIONS

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

# HEADER & SINGLE SEARCH
# =====================================================
with st.container(border=True):

    st.markdown("### 🔍 QE Lookup")
    st.caption("Search a payment description")

    with st.form("qe_search_form"):
        search_text = st.text_input(
            "",
            placeholder='Annual Leave, Parental Leave, Family Violence...'
        )

        submitted = st.form_submit_button(
            "Search",
            use_container_width=False
        )
        
if submitted and search_text:
    loader_placeholder = st.empty()

    with loader_placeholder.container():
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:15px;">
                <div class="spinner" style="
                    border:4px solid rgba(0,0,0,0.1);
                    width:36px;
                    height:36px;
                    border-radius:50%;
                    border-left-color:#0068c9;
                    animation:spin 1s linear infinite;
                "></div>
                <div style="font-weight:100;color:#0068c9;">
                    ✨ Consulting the classification engine...
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% {transform: rotate(0deg);}
                    100% {transform: rotate(360deg);}
                }
            </style>
            """,
            unsafe_allow_html=True
        )

    result = classify_payment(search_text)

    loader_placeholder.empty()

    classification = result.get("QE Classification", "Review")

    if classification == "QE":
        st.success(f"✅ {result.get('Matched Rule','Unknown')} → QE")
    elif classification == "Not QE":
        st.error(f"❌ {result.get('Matched Rule','Unknown')} → Not QE")
    else:
        st.warning(f"⚠️ {result.get('Matched Rule','Unknown')} → Review")

    st.caption(result.get("Reason", ""))

# BULK UPLOAD
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
# PROCESS FILE (FIXED STATE HANDLING)
# =====================================================
if uploaded_file:
    # Clear out historical results if a brand new file is detected
    if "current_file" not in st.session_state or st.session_state["current_file"] != uploaded_file.name:
        st.session_state["current_file"] = uploaded_file.name
        if "bulk_result" in st.session_state:
            del st.session_state["bulk_result"]

    input_df = pd.read_excel(uploaded_file, engine="openpyxl")
    input_df.columns = [str(col).strip() for col in input_df.columns]

    if "Description" not in input_df.columns:
        st.error("Excel file must contain a Description column.")
    else:
        # Only show the process button if we haven't successfully processed the file yet
        if "bulk_result" not in st.session_state:
            if st.button("Process File", type="primary"):
                try:
                    with st.spinner("Classifying file..."):
                        processed_df = classify_bulk(input_df)
                        st.session_state["bulk_result"] = processed_df
                        st.success("Analysis complete!")
                        st.rerun() # Force a rerun to clean up layout states safely
                except Exception as e:
                    st.error(f"Classification Error: {e}")

        # Display results if they exist in state (Independent of the button click state!)
        if "bulk_result" in st.session_state:
            result_df = st.session_state["bulk_result"]

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

# FOOTER BANNER
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 10px; color: #666666; font-size: 0.85rem;">
        <p style="margin-bottom: 4px;">🛡️ <b>No data stored.</b> Files you upload are processed in memory only and discarded immediately after results are returned. Nothing is saved, logged, or transmitted to any third party.</p>
        <p style="font-size: 0.8rem; color: #888888; margin-top: 0;">Designed & Developed by Maruf, Sebgatullah</p>
    </div>
    """,
    unsafe_allow_html=True
)
