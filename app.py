import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from io import BytesIO

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_master():
    return pd.read_excel("QE_Classification_Master_List.xlsx")

master_df = load_master()

# Create lookup helper
master_df["Name_Lower"] = master_df["Name"].str.lower()

# --------------------------------------------------
# MATCHING FUNCTION
# --------------------------------------------------

def classify_payment(search_text):

    if pd.isna(search_text):
        return None

    search_text = str(search_text).strip()

    if search_text == "":
        return None

    search_lower = search_text.lower()

    # -----------------------------------------
    # 1. Exact Match
    # -----------------------------------------

    exact_match = master_df[
        master_df["Name_Lower"] == search_lower
    ]

    if not exact_match.empty:
        row = exact_match.iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # -----------------------------------------
    # 2. Contains Match
    # -----------------------------------------

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

    # -----------------------------------------
    # 3. High Threshold Fuzzy Match
    # -----------------------------------------

    fuzzy_match = process.extractOne(
        search_text,
        master_df["Name"].tolist(),
        scorer=fuzz.WRatio,
        score_cutoff=90
    )

    if fuzzy_match:

        rule_name = fuzzy_match[0]

        row = master_df[
            master_df["Name"] == rule_name
        ].iloc[0]

        return {
            "Matched Rule": row["Name"],
            "QE Classification": row["Type"]
        }

    # -----------------------------------------
    # No Match
    # -----------------------------------------

    return {
        "Matched Rule": "No Match Found",
        "QE Classification": "Review"
    }


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🔍 QE Lookup")

st.caption(
    "ATO Qualifying Earnings Classification Engine"
)

# --------------------------------------------------
# SINGLE SEARCH
# --------------------------------------------------

search_text = st.text_input(
    "",
    placeholder='Type any payment type or keyword — e.g. "car allowance", "jury duty", "overtime", "parental leave"...'
)

if search_text:

    result = classify_payment(search_text)

    st.subheader("Result")

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
            "⚠️ No matching QE rule found. Review required."
        )

# --------------------------------------------------
# BULK UPLOAD
# --------------------------------------------------

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
            "Excel file must contain a column named 'Description'"
        )

    else:

        progress_bar = st.progress(0)

        output_rows = []

        total = len(input_df)

        for i, row in input_df.iterrows():

            description = row["Description"]

            result = classify_payment(description)

            output_rows.append({
                "Description": description,
                "Matched Rule": result["Matched Rule"],
                "QE Classification": result["QE Classification"]
            })

            progress_bar.progress((i + 1) / total)

        result_df = pd.DataFrame(output_rows)

        # --------------------------------------
        # Metrics
        # --------------------------------------

        matched_count = len(
            result_df[
                result_df["QE Classification"] != "Review"
            ]
        )

        review_count = len(
            result_df[
                result_df["QE Classification"] == "Review"
            ]
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Records",
                len(result_df)
            )

        with col2:
            st.metric(
                "Matched",
                matched_count
            )

        with col3:
            st.metric(
                "Review Required",
                review_count
            )

        # --------------------------------------
        # Results
        # --------------------------------------

        if search_text:

    result = classify_payment(search_text)

    st.subheader("Result")

    if result["QE Classification"] != "Review":

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

    else:
        st.warning(
            "⚠️ No matching QE rule found. Review required."
        )

        # --------------------------------------
        # Logs
        # --------------------------------------

        tab1, tab2 = st.tabs(
            ["✅ Matched", "⚠️ Review Required"]
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

        # --------------------------------------
        # DOWNLOAD FILE
        # --------------------------------------

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

            result_df[
                result_df["QE Classification"] != "Review"
            ].to_excel(
                writer,
                sheet_name="Matched",
                index=False
            )

            result_df[
                result_df["QE Classification"] == "Review"
            ].to_excel(
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
