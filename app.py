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
# LOAD MASTER FILE
# ==================================================

@st.cache_data
def load_master():
    df = pd.read_excel("QE_Classification_Master_List.xlsx")
    df["Name_Lower"] = df["Name"].astype(str).str.lower().str.strip()
    return df

master_df = load_master()

# ==================================================
# MATCHING LOGIC
# ==================================================

def classify_payment(search_text):

    if pd.isna(search_text):
        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    search_text = str(search_text).strip()

    if search_text == "":
        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    search_lower = search_text.lower()

    # ---------------------------------------------
    # Exact Match
    # ---------------------------------------------

    exact_match = master_df[
        master_df["Name_Lower"] == search_lower
    ]

    if not exact_match.empty:

        row = exact_match.iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # ---------------------------------------------
    # Contains Match
    # ---------------------------------------------

    contains_match = master_df[
        master_df["Name_Lower"].str.contains(
            search_lower,
            regex=False
        )
    ]

    if len(contains_match) == 1:

        row = contains_match.iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # ---------------------------------------------
    # Fuzzy Match (Strict)
    # ---------------------------------------------

    fuzzy_match = process.extractOne(
        search_text,
        master_df["Name"].tolist(),
        scorer=fuzz.WRatio,
        score_cutoff=90
    )

    if fuzzy_match:

        matched_rule = fuzzy_match[0]

        row = master_df[
            master_df["Name"] == matched_rule
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
    placeholder='Type any payment type or keyword — e.g. "car allowance", "jury duty", "overtime", "parental leave"...'
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
            "⚠️ No confident match found. Review required."
        )

# ==================================================
# BULK CLASSIFICATION
# ==================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.markdown("### Example Excel Format")

example_df = pd.DataFrame({
    "Description": [
        "Parental Leave",
        "Annual Leave",
        "Overtime",
        "Car Allowance"
    ]
})

st.dataframe(
    example_df,
    use_container_width=True,
    hide_index=True
)

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file:

    input_df = pd.read_excel(uploaded_file)

    if "Description" not in input_df.columns:

        st.error(
            "Excel file must contain a column named 'Description'"
        )

    else:

        st.info(
            f"Processing {len(input_df)} records..."
        )

        progress_bar = st.progress(0)

        results = []

        total = len(input_df)

        for idx, row in input_df.iterrows():

            description = row["Description"]

            result = classify_payment(description)

            results.append({
                "Description": description,
                "Matched Rule": result["Matched Rule"],
                "QE Classification": result["QE Classification"]
            })

            progress_bar.progress(
                (idx + 1) / total
            )

        result_df = pd.DataFrame(results)

        # ==========================================
        # SUMMARY METRICS
        # ==========================================

        total_records = len(result_df)

        matched_records = len(
            result_df[
                result_df["QE Classification"] != "Review"
            ]
        )

        review_records = len(
            result_df[
                result_df["QE Classification"] == "Review"
            ]
        )

        qe_records = len(
            result_df[
                result_df["QE Classification"] == "QE"
            ]
        )

        not_qe_records = len(
            result_df[
                result_df["QE Classification"] == "Not QE"
            ]
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total", total_records)

        with col2:
            st.metric("Matched", matched_records)

        with col3:
            st.metric("Review", review_records)

        with col4:
            st.metric("QE", qe_records)

        with col5:
            st.metric("Not QE", not_qe_records)

        # ==========================================
        # RESULTS
        # ==========================================

        st.subheader("Classification Results")

        st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True
        )

        # ==========================================
        # MATCH LOGS
        # ==========================================

        tab1, tab2 = st.tabs([
            "✅ Matched",
            "⚠️ Review Required"
        ])

        with tab1:

            matched_df = result_df[
                result_df["QE Classification"] != "Review"
            ]

            st.dataframe(
                matched_df,
                use_container_width=True,
                hide_index=True
            )

        with tab2:

            review_df = result_df[
                result_df["QE Classification"] == "Review"
            ]

            st.dataframe(
                review_df,
                use_container_width=True,
                hide_index=True
            )

        # ==========================================
        # DOWNLOAD FILE
        # ==========================================

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
            label="📥 Download Results",
            data=output.getvalue(),
            file_name="QE_Classification_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
