import streamlit as st
import pandas as pd
from openai import OpenAI
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
# OPENAI
# =====================================================

with st.sidebar:

    st.header("AI Settings")

    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password"
    )

if not openai_api_key:

    st.info(
        "Enter your OpenAI API key in the sidebar."
    )

    st.stop()

client = OpenAI(
    api_key=openai_api_key
)

# =====================================================
# AI CLASSIFICATION
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
You are an Australian payroll specialist.

Using ONLY ATO Payday Super 2026 Qualifying Earnings (QE) principles.

Review the payment description and determine:

1. Most likely payment type.
2. Whether it is:
   - QE
   - Not QE
   - Review

Examples:

Annual Leave = QE
Sick Leave = QE
Personal Leave = QE
Family And Domestic Violence Leave = QE
Commission = QE

Parental Leave = Not QE
Maternity Leave = Not QE
Paternity Leave = Not QE
Government Paid Parental Leave = Not QE
Overtime = Not QE
Jury Duty = Not QE
Termination Payment = Not QE

Car Allowance = Review
Meal Allowance = Review
Phone Allowance = Review

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

        response = client.chat.completions.create(
            model="gpt-5-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Australian payroll "
                        "and superannuation specialist."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = (
            response
            .choices[0]
            .message
            .content
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

    result = classify_payment(search_text)

    if result["QE Classification"] == "QE":

        st.success(
            f"✅ {result['Matched Rule']} → QE"
        )

    elif result["QE Classification"] == "Not QE":

        st.error(
            f"❌ {result['Matched Rule']} → Not QE"
        )

    else:

        st.warning(
            f"⚠️ {result['Matched Rule']} → Review"
        )

    if result["Reason"]:

        st.caption(
            result["Reason"]
        )

# =====================================================
# BULK UPLOAD
# =====================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.info(
    "Download the template below, populate the Description column and upload the completed file."
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
    label="📄 Download Template",
    data=template_output.getvalue(),
    file_name="QE_Template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption(
    "Required column: Description"
)

# =====================================================
# EXAMPLE
# =====================================================

with st.expander("📋 Example Excel Format"):

    example_df = pd.DataFrame({
        "Description": [
            "Parental Leave Half Pay",
            "Family Violence Leave",
            "PILON",
            "Annual Leave",
            "Car Allowance"
        ]
    })

    st.dataframe(
        example_df,
        hide_index=True,
        use_container_width=True
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
            "Excel file must contain a column named 'Description'."
        )

    else:

        total = len(input_df)

        if total == 0:

            st.warning(
                "The uploaded file contains no records."
            )

        else:

            progress = st.progress(0)

            results = []

            for idx, row in input_df.iterrows():

                result = classify_payment(
                    row["Description"]
                )

                results.append({
                    "Description": row["Description"],
                    "Matched Rule": result["Matched Rule"],
                    "QE Classification": result["QE Classification"],
                    "Reason": result["Reason"]
                })

                progress.progress(
                    (idx + 1) / total
                )

            result_df = pd.DataFrame(results)

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

            col1.metric("Total", len(result_df))
            col2.metric("QE", len(qe_df))
            col3.metric("Not QE", len(not_qe_df))
            col4.metric("Review", len(review_df))

            st.subheader("Results")

            tab1, tab2, tab3 = st.tabs(
                [
                    f"✅ QE ({len(qe_df)})",
                    f"❌ Not QE ({len(not_qe_df)})",
                    f"⚠️ Review ({len(review_df)})"
                ]
            )

            with tab1:

                st.success(
                    f"{len(qe_df)} record(s) classified as QE"
                )

                st.dataframe(
                    qe_df,
                    hide_index=True,
                    use_container_width=True
                )

            with tab2:

                st.error(
                    f"{len(not_qe_df)} record(s) classified as Not QE"
                )

                st.dataframe(
                    not_qe_df,
                    hide_index=True,
                    use_container_width=True
                )

            with tab3:

                st.warning(
                    f"{len(review_df)} record(s) require review"
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

                input_df.to_excel(
                    writer,
                    sheet_name="Original Upload",
                    index=False
                )

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
