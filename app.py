import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import json

# PAGE CONFIG

st.set_page_config(
    page_title="SuperQE",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# DESIGN SYSTEM
st.markdown("""
<style>

/* --------------------------------------------------
   STREAMLIT CLEANUP
-------------------------------------------------- */

header[data-testid="stHeader"]{
    display:none;
}

            
#MainMenu{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

/* --------------------------------------------------
   APP
-------------------------------------------------- */

.stApp{
    background:#F5F3EB;
}

.block-container{
    max-width:1100px;
    padding-top:1rem;
    padding-bottom:2rem;
}

/* --------------------------------------------------
   TYPOGRAPHY
-------------------------------------------------- */

html, body, [class*="css"]{
    font-family: Inter, sans-serif;
}

h1,h2,h3{
    color:#0F2940;
}

/* --------------------------------------------------
   NAVIGATION
-------------------------------------------------- */

.superqe-nav{

    background:white;

    border:1px solid #D8DDD6;

    border-radius:18px;

    padding:14px 24px;

    margin-bottom:24px;

    display:flex;

    justify-content:space-between;

    align-items:center;
}

.superqe-brand{

    font-size:34px;

    font-weight:800;

    color:#0F2940;
}

.superqe-accent{
    color:#07B59B;
}

.superqe-nav-text{

    color:#6B7280;

    font-size:14px;
}
            
* Entered text */
/* Input text */
div[data-baseweb="input"] input {
    color: #0F2940 !important;
    background-color: #FFFFFF !important;
    caret-color: #07B59B !important;
}

/* Placeholder */
div[data-baseweb="input"] input::placeholder {
    color: #94A3B8 !important;
    opacity: 1 !important;
}

/* Password field */
div[data-baseweb="input"] input[type="password"] {
    -webkit-text-fill-color: #0F2940 !important;
}
            
input {
    caret-color: #07B59B !important;
}
            

/* File uploader text */
[data-testid="stFileUploader"] * {
    color: #0F2940 !important;
}

[data-testid="metric-container"] * {
    color: #0F2940 !important;
}
            
.stTabs [data-baseweb="tab"] {
    color: #0F2940 !important;
}

.stTabs [aria-selected="true"] {
    color: #07B59B !important;
}

[data-testid="stDataFrame"] {
    color: #0F2940 !important;
}
            
label {
    color: #0F2940 !important;
}
            
[data-testid="stSpinner"] * {
    color: #2563EB !important;
}
            

/* --------------------------------------------------
   CARDS
-------------------------------------------------- */

div[data-testid="stVerticalBlockBorderWrapper"]{

    border-radius:20px;

    border:1px solid #D8DDD6;

    background:white;
}

/* --------------------------------------------------
   INPUTS
-------------------------------------------------- */

.stTextInput input{

    border-radius:12px;

    border:1px solid #D8DDD6;

    min-height:52px;

    background:white;

    color:#0F2940;
}

/* --------------------------------------------------
   BUTTONS
-------------------------------------------------- */
            
            

.stButton button{

    height:48px;

    border-radius:12px;

    border:1px solid #D8DDD6;

    background:white;

    color:#0F2940;

    font-weight:600;
}

.stButton button:hover{

    border-color:#07B59B;

    color:#07B59B;
}

/* --------------------------------------------------
   FILE UPLOADER
-------------------------------------------------- */

[data-testid="stFileUploader"] {
    border: 1px dashed #D8DDD6;
    border-radius: 16px;
    background: #0F2940;
}

[data-testid="stFileUploader"] * {
    color: white !important;
}

/* --------------------------------------------------
   METRICS
-------------------------------------------------- */

[data-testid="metric-container"]{

    background:white;

    border:1px solid #D8DDD6;

    border-radius:12px;

    padding:12px;
}

/* --------------------------------------------------
   MOBILE
-------------------------------------------------- */

@media(max-width:768px){

    .superqe-brand{
        font-size:26px;
    }

    .block-container{
        padding-top:0.5rem;
    }
}
            
.stMarkdown,
.stMarkdown p,
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3 {
    color: #0F2940 !important;
}
           
div.stButton > button[kind="primary"]:hover {
    background-color: #1668a3;
    color: black !important;
    border: 1px solid #1668a3;
}
</style>
""", unsafe_allow_html=True)



# ============================================================
# TOP BAR
# ============================================================

st.markdown("""
<div class="superqe-nav">

<div class="superqe-brand">
Super<span class="superqe-accent">QE</span>
</div>

</div>
""", unsafe_allow_html=True)

# ============================================================
# API CONFIGURATION
# ============================================================

with st.container(border=True):

    st.markdown("""
<div style="display:flex; align-items:center; gap:15px;">
    <h5 style="margin:0;">Gemini API</h5>
    <a href="https://aistudio.google.com/app/apikey" target="_blank"
       style="font-size:14px;">
       🔑 Get Gemini API Key
    </a>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([8,2])

    with col1:

        gemini_api_key = st.text_input(
            "",
            placeholder="Enter Gemini API Key",
            label_visibility="collapsed",
            type="password"
        )

    with col2:

        submit_key = st.button(
            "Continue",
            use_container_width=True
        )

# ============================================================
# API STATE
# ============================================================

if submit_key and gemini_api_key:

    st.session_state["gemini_api_key"] = gemini_api_key
    st.session_state["api_key_submitted"] = True

if not st.session_state.get("api_key_submitted", False):

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

# ------------------------
# HEADER & SINGLE SEARCH
# QE Lookup Card

result_placeholder = st.container(border=True)

with result_placeholder:
    
    st.markdown("""
<div class="section-label">
    Pay-Code Lookup
</div>
<div style="margin-top: 4px;">
    Search a payment description and classify it using ATO QE rules
</div>
""", unsafe_allow_html=True)

with st.form("qe_search_form"):
    search_text = st.text_input(
        label="Payment description",
        label_visibility="collapsed",
        placeholder="Annual Leave, Parental Leave, TOIL..."
    )

    submitted = st.form_submit_button("Search")

    # Run search
    if submitted and search_text:

        loader_placeholder = st.empty()

        # Loader inside card
        with loader_placeholder:
            st.markdown(
                """
                <div style="
                    display:flex;
                    align-items:center;
                    gap:12px;
                    padding:10px 0;
                    color:#60a5fa;
                ">
                    <div style="
                        border:3px solid rgba(255,255,255,0.15);
                        width:22px;
                        height:22px;
                        border-radius:50%;
                        border-left-color:#60a5fa;
                        animation:spin 0.8s linear infinite;
                    ">
                    </div>
                        Consulting classification engine...
                </div>

                <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        # Classification
        result = classify_payment(search_text)

        # Remove loader
        loader_placeholder.empty()

        classification = result.get("QE Classification", "Review")
        rule = result.get("Matched Rule", "Unknown")
        reason = result.get("Reason", "")
        
        # Result card
        if classification == "QE":
            st.markdown(
                f"""
                <div style="
                    padding:16px;
                    border-radius:12px;
                    border-left:4px solid #22c55e;
                    background:rgba(34,197,94,0.08);
                    margin-top:10px;
                ">
                    <div style="font-size:18px;font-weight:600;color:#22c55e;">
                        ✅ QE
                    </div>
                    <div style="margin-top:6px;">
                        <strong>{rule}</strong>
                    </div>
                    <div style="margin-top:6px;font-size:14px;opacity:0.8;">
                        {reason}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif classification == "Not QE":
            st.markdown(
                f"""
                <div style="
                    padding:16px;
                    border-radius:12px;
                    border-left:4px solid #ef4444;
                    background:rgba(239,68,68,0.08);
                    margin-top:10px;
                ">
                    <div style="font-size:18px;font-weight:600;color:#ef4444;">
                        ❌ Not QE
                    </div>
                    <div style="margin-top:6px;">
                        <strong>{rule}</strong>
                    </div>
                    <div style="margin-top:6px;font-size:14px;opacity:0.8;">
                        {reason}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div style="
                    padding:16px;
                    border-radius:12px;
                    border-left:4px solid #f59e0b;
                    background:rgba(245,158,11,0.08);
                    margin-top:10px;
                ">
                    <div style="font-size:18px;font-weight:600;color:#f59e0b;">
                        ⚠️ Review Required
                    </div>
                    <div style="margin-top:6px;">
                        <strong>{rule}</strong>
                    </div>
                    <div style="margin-top:6px;font-size:14px;opacity:0.8;">
                        {reason}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# BULK UPLOAD

with st.container(border=True):

    st.markdown("""
<div class="section-label">
    Bulk Classification
</div>
<div style="margin-top: 4px;">
    Upload a payroll file and classify pay descriptions in bulk

</div>
""", unsafe_allow_html=True)

    template_df = pd.DataFrame({"Description": []})
    template_output = BytesIO()

    with pd.ExcelWriter(template_output, engine="openpyxl") as writer:
        template_df.to_excel(writer, sheet_name="Template", index=False)

    st.download_button(
        "📄 Download Template",
        data=template_output.getvalue(),
        file_name="QE_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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

        input_df = pd.read_excel(uploaded_file, engine="openpyxl")
        input_df.columns = [str(col).strip() for col in input_df.columns]

        if "Description" not in input_df.columns:
            st.error("Excel file must contain a Description column.")

        else:
            if "bulk_result" not in st.session_state:
                if st.button("Process File", type="primary"):
                    try:
                        with st.spinner("Classifying file..."):
                            processed_df = classify_bulk(input_df)
                            st.session_state["bulk_result"] = processed_df

                        st.success("Analysis complete!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Classification Error: {e}")

            if "bulk_result" in st.session_state:

                result_df = st.session_state["bulk_result"]

                if "QE Classification" not in result_df.columns:
                    result_df["QE Classification"] = "Review"

                qe_df = result_df[result_df["QE Classification"] == "QE"]
                not_qe_df = result_df[result_df["QE Classification"] == "Not QE"]
                review_df = result_df[result_df["QE Classification"] == "Review"]

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
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                if st.button("🧹 Clear Results"):
                    del st.session_state["bulk_result"]
                    st.rerun()

# FOOTER BANNER
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 10px; color: #666666; font-size: 0.85rem;">
        <p style="margin-bottom: 4px;">🛡️ <b>No data stored.</b> Files you upload are processed in memory only and discarded immediately after results are returned. Nothing is saved, logged, or transmitted to any third party.</p>
        <p style="font-size: 0.8rem; color: #888888; margin-top: 0;">Designed & Developed by Maruf, Sebgatullah</p>
    Powered by Google Gemini 
    </div>
    """,
    unsafe_allow_html=True
)
