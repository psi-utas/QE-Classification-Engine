import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process
from io import BytesIO

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# --------------------------------------------------
# Load Master Data
# --------------------------------------------------
@st.cache_data
def load_master():
    return pd.read_excel("QE_Classification_Master_List.xlsx")

master_df = load_master()

# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("🔍 QE Lookup")

st.caption(
    "Search a payment type or upload an Excel file for bulk QE classification."
)

# --------------------------------------------------
# Single Search
# --------------------------------------------------
search_text = st.text_input(
    "",
    placeholder='Type any payment type or keyword — e.g. "car allowance", "jury duty", "overtime", "parental leave"...'
)

if search_text:

    match = process.extractOne(
        search_text,
        master_df["Name"].tolist(),
        scorer=fuzz.token_sort_ratio
    )

    if match:

        payment_name = match[0]
        confidence = round(match[1], 2)

        row = master_df[
            master_df["Name"] == payment_name
        ].iloc[0]

        st.subheader("Result")

        if row["Type"] == "QE":
            st.success(
                f"✅ {payment_name} → QE (Confidence: {confidence}%)"
            )

        elif row["Type"] == "Not QE":
            st.error(
                f"❌ {payment_name} → Not QE (Confidence: {confidence}%)"
            )

        else:
            st.warning(
                f"⚠️ {payment_name} → Review (Confidence: {confidence}%)"
            )

# --------------------------------------------------
# Bulk Upload
# --------------------------------------------------
st.divider()

st.subheader("📤 Bulk QE Classification")

st.markdown("### Example Excel Format")

example_df = pd.DataFrame({
    "Description": [
        "Parental Leave",
        "Overtime",
        "Annual Leave",
        "Car Allowance",
        "Sign-on Bonus"
    ]
})

st.dataframe(example_df, hide_index=True)

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

threshold = st.slider(
    "Minimum Match Confidence (%)",
    min_value=50,
    max_value=100,
    value=80
)

if uploaded_file:

    input_df = pd.read_excel(uploaded_file)

    if "Description" not in input_df.columns:

        st.error(
            "Excel file must contain a column named 'Description'"
        )

    else:

        progress = st.progress(0)

        matched = []
        unmatched = []

        results = []

        total = len(input_df)

        for i, desc in enumerate(input_df["Description"]):

            if pd.isna(desc):

                results.append(
                    [desc, "", "", "Review"]
                )

                continue

            match = process.extractOne(
                str(desc),
                master_df["Name"].tolist(),
                scorer=fuzz.token_sort_ratio
            )

            if match:

                master_name = match[0]
                confidence = round(match[1], 2)

                if confidence >= threshold:

                    qe_type = master_df.loc[
                        master_df["Name"] == master_name,
                        "Type"
                    ].iloc[0]

                    matched.append(desc)

                else:

                    qe_type = "Review"

                    unmatched.append(desc)

            else:

                master_name = ""
                confidence = 0
                qe_type = "Review"

                unmatched.append(desc)

            results.append([
                desc,
                master_name,
                confidence,
                qe_type
            ])

            progress.progress((i + 1) / total)

        output_df = pd.DataFrame(
            results,
            columns=[
                "Description",
                "Matched Value",
                "Confidence",
                "QE Classification"
            ]
        )

        st.success(
            f"Processed {len(output_df)} records"
        )

        # ------------------------------------------
        # Metrics
        # ------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Matched",
                len(matched)
            )

        with col2:
            st.metric(
                "Review Required",
                len(unmatched)
            )

        with col3:
            st.metric(
                "Total",
                len(output_df)
            )

        # ------------------------------------------
        # Results
        # ------------------------------------------

        st.subheader("Classification Results")

        st.dataframe(
            output_df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # Logs
        # ------------------------------------------

        tab1, tab2 = st.tabs([
            "✅ Matched",
            "⚠️ Review Required"
        ])

        with tab1:
            st.dataframe(
                output_df[
                    output_df["QE Classification"] != "Review"
                ],
                use_container_width=True
            )

        with tab2:
            st.dataframe(
                output_df[
                    output_df["QE Classification"] == "Review"
                ],
                use_container_width=True
            )

        # ------------------------------------------
        # Download Output
        # ------------------------------------------

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            output_df.to_excel(
                writer,
                sheet_name="Results",
                index=False
            )

            output_df[
                output_df["QE Classification"] != "Review"
            ].to_excel(
                writer,
                sheet_name="Matched",
                index=False
            )

            output_df[
                output_df["QE Classification"] == "Review"
            ].to_excel(
                writer,
                sheet_name="Review Required",
                index=False
            )

        st.download_button(
            label="📥 Download Classified Results",
            data=output.getvalue(),
            file_name="QE_Classification_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
