import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from io import BytesIO

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# ==================================================
# LOAD MASTER DATA
# ==================================================

@st.cache_data
def load_master():

    df = pd.read_excel(
        "QE_Classification_Master_List.xlsx",
        engine="openpyxl"
    )

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    required_columns = [
        "Name",
        "Type",
        "Keywords"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        st.error(
            f"Missing required columns: {', '.join(missing)}"
        )

        st.write("Columns found:")
        st.write(df.columns.tolist())

        st.stop()

    df["Name"] = (
        df["Name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Type"] = (
        df["Type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Keywords"] = (
        df["Keywords"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Name_Lower"] = (
        df["Name"]
        .str.lower()
    )

    return df


master_df = load_master()

# ==================================================
# CLASSIFICATION FUNCTION
# ==================================================

def classify_payment(search_text):

    if pd.isna(search_text):

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    search_text = str(search_text).strip().lower()

    if search_text == "":

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    # ---------------------------------------------
    # 1. Exact Name Match
    # ---------------------------------------------

    exact_match = master_df[
        master_df["Name_Lower"] == search_text
    ]

    if not exact_match.empty:

        row = exact_match.iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # ---------------------------------------------
    # 2. Exact Keyword Match
    # ---------------------------------------------

    for _, row in master_df.iterrows():

        keywords = [
            k.strip().lower()
            for k in row["Keywords"].split(";")
            if k.strip()
        ]

        if search_text in keywords:

            return {
                "Matched Rule": row["Name"],
                "QE Classification": row["Type"]
            }

    # ---------------------------------------------
    # 3. Keyword Contained In Search
    # Example:
    # "Parental Leave Half Pay"
    # should find "parental leave"
    # ---------------------------------------------

    matches = []

    for _, row in master_df.iterrows():

        keywords = [
            k.strip().lower()
            for k in row["Keywords"].split(";")
            if k.strip()
        ]

        for keyword in keywords:

            if keyword in search_text:

                matches.append({
                    "Length": len(keyword),
                    "Rule": row["Name"],
                    "Type": row["Type"]
                })

    if matches:

        matches = sorted(
            matches,
            key=lambda x: x["Length"],
            reverse=True
        )

        best_match = matches[0]

        return {
            "Matched Rule": best_match["Rule"],
            "QE Classification": best_match["Type"]
        }

    # ---------------------------------------------
    # 4. Fuzzy Match (Last Resort)
    # ---------------------------------------------

    fuzzy_match = process.extractOne(
        search_text,
        master_df["Name"].tolist(),
        scorer=fuzz.partial_ratio,
        score_cutoff=95
    )

    if fuzzy_match:

        matched_name = fuzzy_match[0]

        row = master_df[
            master_df["Name"] == matched_name
        ].iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # ---------------------------------------------
    # No Match
    # ---------------------------------------------

    return {
        "Matched Rule": "No Match Found",
        "QE Classification": "Review"
    }


# ==================================================
# HEADER
# ==================================================

st.title("🔍 QE Lookup")

st.caption(
    "ATO Qualifying Earnings Classification Engine"
)

# ==================================================
# SEARCH
# ==================================================

search_text = st.text_input(
    "",
    placeholder='Type payment description e.g. "Parental Leave Half Pay", "PILON", "FDVL", "Overtime", "Car Allowance"...'
)

if search_text:

    result = classify_payment(search_text)

    st.subheader("Result")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Matched Rule",
            result["Matched Rule"]
        )

    with col2:

        st.metric(
            "Classification",
            result["QE Classification"]
        )

# ==================================================
# BULK UPLOAD
# ==================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.markdown("### Example Excel Format")

example_df = pd.DataFrame({
    "Description": [
        "Parental Leave Half Pay",
        "Annual Leave",
        "Overtime",
        "PILON",
        "FDVL",
        "Car Allowance"
    ]
})

st.dataframe(
    example_df,
    hide_index=True,
    use_container_width=True
)

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file:

    input_df = pd.read_excel(
        uploaded_file,
        engine="openpyxl"
    )

    if "Description" not in input_df.columns:

        st.error(
            "Excel file must contain a Description column."
        )

    else:

        progress_bar = st.progress(0)

        results = []

        total_records = len(input_df)

        for i, row in input_df.iterrows():

            result = classify_payment(
                row["Description"]
            )

            results.append({
                "Description": row["Description"],
                "Matched Rule": result["Matched Rule"],
                "QE Classification": result["QE Classification"]
            })

            progress_bar.progress(
                (i + 1) / total_records
            )

        result_df = pd.DataFrame(results)

        # ======================================
        # Metrics
        # ======================================

        qe_count = len(
            result_df[
                result_df["QE Classification"] == "QE"
            ]
        )

        not_qe_count = len(
            result_df[
                result_df["QE Classification"] == "Not QE"
            ]
        )

        review_count = len(
            result_df[
                result_df["QE Classification"] == "Review"
            ]
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("QE", qe_count)

        with col2:
            st.metric("Not QE", not_qe_count)

        with col3:
            st.metric("Review", review_count)

        # ======================================
        # Results
        # ======================================

        st.subheader("Classification Results")

        st.dataframe(
            result_df,
            hide_index=True,
            use_container_width=True
        )

        matched_df = result_df[
            result_df["QE Classification"] != "Review"
        ]

        review_df = result_df[
            result_df["QE Classification"] == "Review"
        ]

        tab1, tab2 = st.tabs(
            [
                "✅ Matched",
                "⚠️ Review Required"
            ]
        )

        with tab1:

            st.dataframe(
                matched_df,
                hide_index=True,
                use_container_width=True
            )

        with tab2:

            st.dataframe(
                review_df,
                hide_index=True,
                use_container_width=True
            )

        # ======================================
        # DOWNLOAD
        # ======================================

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

            matched_df.to_excel(
                writer,
                sheet_name="Matched",
                index=False
            )

            review_df.to_excel(
                writer,
                sheet_name="Review Required",
                index=False
            )

        st.download_button(
            "📥 Download Results",
            data=output.getvalue(),
            file_name="QE_Classification_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
