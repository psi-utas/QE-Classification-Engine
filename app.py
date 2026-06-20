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
# LOAD DATA
# ==================================================

@st.cache_data
def load_master():

    df = pd.read_excel(
        "QE_Classification_Master_List.xlsx"
    )

    df["Name"] = df["Name"].fillna("")
    df["Type"] = df["Type"].fillna("")
    df["Keyword"] = df["Keyword"].fillna("")

    df["Name_Lower"] = (
        df["Name"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return df

master_df = load_master()

# ==================================================
# MATCHING FUNCTION
# ==================================================

def classify_payment(search_text):

    if pd.isna(search_text):
        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    search_text = str(search_text).lower().strip()

    if not search_text:
        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    # ------------------------------------------
    # 1. Exact Name Match
    # ------------------------------------------

    exact = master_df[
        master_df["Name_Lower"] == search_text
    ]

    if not exact.empty:

        row = exact.iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # ------------------------------------------
    # 2. Exact Keyword Match
    # ------------------------------------------

    for _, row in master_df.iterrows():

        keywords = [
            k.strip().lower()
            for k in str(row["Keywords"]).split(";")
            if k.strip()
        ]

        if search_text in keywords:

            return {
                "Matched Rule": row["Name"],
                "QE Classification": row["Type"]
            }

    # ------------------------------------------
    # 3. Keyword Contained In Search Text
    # ------------------------------------------

    matches = []

    for _, row in master_df.iterrows():

        keywords = [
            k.strip().lower()
            for k in str(row["Keywords"]).split(";")
            if k.strip()
        ]

        for keyword in keywords:

            if keyword and keyword in search_text:

                matches.append(
                    (
                        len(keyword),
                        row["Name"],
                        row["Type"]
                    )
                )

    if matches:

        matches.sort(reverse=True)

        return {
            "Matched Rule": matches[0][1],
            "QE Classification": matches[0][2]
        }

    # ------------------------------------------
    # 4. Fuzzy Match (Last Resort)
    # ------------------------------------------

    fuzzy_match = process.extractOne(
        search_text,
        master_df["Name"].tolist(),
        scorer=fuzz.partial_ratio,
        score_cutoff=92
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

    # ------------------------------------------
    # No Match
    # ------------------------------------------

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
# SINGLE SEARCH
# ==================================================

search_text = st.text_input(
    "",
    placeholder='Type payment type e.g. "Parental Leave Half Pay", "Car Allowance", "PILON", "FDVL"...'
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

    if result["QE Classification"] == "QE":

        st.success("✅ Qualifying Earnings")

    elif result["QE Classification"] == "Not QE":

        st.error("❌ Not Qualifying Earnings")

    else:

        st.warning(
            "⚠️ Review Required"
        )

# ==================================================
# BULK CLASSIFICATION
# ==================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.markdown(
    """
### Example Excel Format

| Description |
|-------------|
| Parental Leave Half Pay |
| Annual Leave |
| PILON |
| FDVL |
| Car Allowance |
"""
)

example_df = pd.DataFrame({
    "Description": [
        "Parental Leave Half Pay",
        "Annual Leave",
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

    input_df = pd.read_excel(uploaded_file)

    if "Description" not in input_df.columns:

        st.error(
            "Excel file must contain a Description column."
        )

    else:

        progress = st.progress(0)

        results = []

        total = len(input_df)

        for idx, row in input_df.iterrows():

            result = classify_payment(
                row["Description"]
            )

            results.append({
                "Description": row["Description"],
                "Matched Rule": result["Matched Rule"],
                "QE Classification": result["QE Classification"]
            })

            progress.progress(
                (idx + 1) / total
            )

        result_df = pd.DataFrame(results)

        # Metrics

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

        c1, c2, c3 = st.columns(3)

        c1.metric("QE", qe_count)
        c2.metric("Not QE", not_qe_count)
        c3.metric("Review", review_count)

        st.subheader("Results")

        st.dataframe(
            result_df,
            hide_index=True,
            use_container_width=True
        )

        tab1, tab2 = st.tabs(
            [
                "✅ Matched",
                "⚠️ Review"
            ]
        )

        with tab1:

            st.dataframe(
                result_df[
                    result_df["QE Classification"] != "Review"
                ],
                hide_index=True,
                use_container_width=True
            )

        with tab2:

            st.dataframe(
                result_df[
                    result_df["QE Classification"] == "Review"
                ],
                hide_index=True,
                use_container_width=True
            )

        # Download File

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
