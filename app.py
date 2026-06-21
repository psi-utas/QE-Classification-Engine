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
# GEMINI
# =====================================================

genai.configure(
    api_key=gemini_api_key
)

MODEL_NAME = "gemini-3.1-flash-lite"

model = genai.GenerativeModel(
    MODEL_NAME
)

# =====================================================
# SINGLE CLASSIFICATION
# =====================================================

def classify_payment(description):

    prompt = f"""
You are an Australian payroll and superannuation specialist.

Using ONLY ATO Payday Super 2026 Qualifying Earnings (QE) principles,
classify the payroll payment description below.

Return JSON only.

{{
  "Matched Rule":"",
  "QE Classification":"QE|Not QE|Review",
  "Reason":""
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

        return json.loads(content)

    except Exception as e:

        return {
            "Matched Rule": "AI Error",
            "QE Classification": "Review",
            "Reason": str(e)
        }

# =====================================================
# BULK CLASSIFICATION
# =====================================================

def classify_bulk(input_df):

    descriptions = (
        input_df["Description"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    description_text = "\n".join(
        [
            f"{i+1}. {d}"
            for i, d in enumerate(descriptions)
        ]
    )

    prompt = f"""
You are an Australian payroll and superannuation specialist.

Using ATO Payday Super 2026 Qualifying Earnings principles.

Classify EACH payroll description below.

Allowed classifications:

QE
Not QE
Review

Return ONLY a JSON array.

Example:

[
  {{
    "Description":"Annual Leave",
    "Matched Rule":"Annual Leave",
    "QE Classification":"QE",
    "Reason":"Paid leave forms part of QE."
  }}
]

Descriptions:

{description_text}
"""

    response = model.generate_content(
        prompt
    )

    content = (
        response.text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    results = json.loads(content)

    return pd.DataFrame(results)

# =====================================================
# HEADER
# =====================================================

st.title("🔍 QE Lookup")

search_text = st.text_input(
    "",
    placeholder='Type payment description e.g. "Parental Leave Half Pay", "Family Violence Leave", "PILON"...'
)

# =====================================================
# SEARCH RESULT
# =====================================================

if search_text:

    result = classify_payment(
        search_text
    )

    classification = result.get(
        "QE Classification",
        "Review"
    )

    if classification == "QE":

        st.success(
            f"✅ {result.get('Matched Rule','Unknown')} → QE"
        )

    elif classification == "Not QE":

        st.error(
            f"❌ {result.get('Matched Rule','Unknown')} → Not QE"
        )

    else:

        st.warning(
            f"⚠️ {result.get('Matched Rule','Unknown')} → Review"
        )

    st.caption(
        result.get(
            "Reason",
            ""
        )
    )

# =====================================================
# BULK UPLOAD
# =====================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.info(
    "Download the template, complete the Description column and upload."
)

# =====================================================
# TEMPLATE
# =====================================================

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

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Upload Completed Template",
    type=["xlsx"]
)

if uploaded_file:

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

        try:

            with st.spinner(
                "Classifying payroll descriptions..."
            ):

                result_df = classify_bulk(
                    input_df
                )

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

            tab1, tab2, tab3 = st.tabs([
                f"✅ QE ({len(qe_df)})",
                f"❌ Not QE ({len(not_qe_df)})",
                f"⚠️ Review ({len(review_df)})"
            ])

            with tab1:

                st.success(
                    f"{len(qe_df)} record(s)"
                )

                st.dataframe(
                    qe_df,
                    hide_index=True,
                    use_container_width=True
                )

            with tab2:

                st.error(
                    f"{len(not_qe_df)} record(s)"
                )

                st.dataframe(
                    not_qe_df,
                    hide_index=True,
                    use_container_width=True
                )

            with tab3:

                st.warning(
                    f"{len(review_df)} record(s)"
                )

                st.dataframe(
                    review_df,
                    hide_index=True,
                    use_container_width=True
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

                qe_df.to_excel(
                    writer,
                    sheet_name="QE",
                    index=False
                )

                not_qe_df.to_excel(
                    writer,
                    sheet_name="Not QE",
                    index=False
                )

                review_df.to_excel(
                    writer,
                    sheet_name="Review",
                    index=False
                )

            st.download_button(
                "📥 Download Results",
                data=output.getvalue(),
                file_name="QE_Classification_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:

            st.error(
                f"Classification Error: {e}"
            )
