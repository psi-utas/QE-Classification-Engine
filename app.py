import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# =====================================================
# LOAD MASTER DATA
# =====================================================

@st.cache_data
def load_master():

    df = pd.read_excel(
        "QE_Classification_Master_List.xlsx",
        engine="openpyxl"
    )

    df.columns = df.columns.str.strip()

    required = [
        "Name",
        "Type",
        "Keywords"
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        st.error(
            f"Missing columns: {', '.join(missing)}"
        )
        st.stop()

    df = df.fillna("")

    return df


master_df = load_master()

# =====================================================
# BUILD LOOKUP
# =====================================================

lookup = []

for _, row in master_df.iterrows():

    lookup.append({
        "keyword": str(row["Name"]).lower(),
        "name": row["Name"],
        "type": row["Type"]
    })

    for keyword in str(row["Keywords"]).split(";"):

        keyword = keyword.strip().lower()

        if keyword:

            lookup.append({
                "keyword": keyword,
                "name": row["Name"],
                "type": row["Type"]
            })

# =====================================================
# CLASSIFICATION
# =====================================================

def classify_payment(text):

    if pd.isna(text):

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    text = str(text).lower().strip()

    if not text:

        return {
            "Matched Rule": "No Match Found",
            "QE Classification": "Review"
        }

    # Exact Match

    for item in lookup:

        if text == item["keyword"]:

            return {
                "Matched Rule": item["name"],
                "QE Classification": item["type"]
            }

    # Contains Match

    matches = []

    for item in lookup:

        keyword = item["keyword"]

        if keyword in text:

            matches.append(
                (
                    len(keyword),
                    item["name"],
                    item["type"]
                )
            )

    if matches:

        matches.sort(
            key=lambda x: x[0],
            reverse=True
        )

        best = matches[0]

        return {
            "Matched Rule": best[1],
            "QE Classification": best[2]
        }

    # Fuzzy Match

    match = process.extractOne(
        text,
        [x["keyword"] for x in lookup],
        scorer=fuzz.token_set_ratio
    )

    if match and match[1] >= 85:

        keyword = match[0]

        for item in lookup:

            if item["keyword"] == keyword:

                return {
                    "Matched Rule": item["name"],
                    "QE Classification": item["type"]
                }

    return {
        "Matched Rule": "No Match Found",
        "QE Classification": "Review"
    }


# =====================================================
# HEADER
# =====================================================

st.title("🔍 QE Lookup")

search_text = st.text_input(
    "",
    placeholder='Type payment description e.g. "Parental Leave Half Pay", "Family Violence Leave", "FDVL", "PILON"...'
)

# =====================================================
# SEARCH RESULT
# =====================================================

if search_text:

    result = classify_payment(search_text)

    st.write(f"**Matched Rule:** {result['Matched Rule']}")

    if result["QE Classification"] == "QE":

        st.success("✅ QE")

    elif result["QE Classification"] == "Not QE":

        st.error("❌ Not QE")

    else:

        st.warning("⚠️ Review")

# =====================================================
# BULK UPLOAD
# =====================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

st.info(
    "Download the template below and populate the Description column with payment descriptions."
)

# TEMPLATE DOWNLOAD
# ----------------------------------

template_df = pd.DataFrame(
    columns=["Description"]
)

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

uploaded_file = st.file_uploader(
    "Upload Completed Template",
    type=["xlsx"]
)

with st.expander("📋 Example Excel Format", expanded=False):

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
            "Excel must contain a 'Description' column."
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

        qe_df = result_df[
            result_df["QE Classification"] == "QE"
        ]

        not_qe_df = result_df[
            result_df["QE Classification"] == "Not QE"
        ]

        review_df = result_df[
            result_df["QE Classification"] == "Review"
        ]

        # ==================================
        # METRICS
        # ==================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total",
                len(result_df)
            )

        with col2:
            st.metric(
                "QE",
                len(qe_df)
            )

        with col3:
            st.metric(
                "Not QE",
                len(not_qe_df)
            )

        with col4:
            st.metric(
                "Review",
                len(review_df)
            )

        # ==================================
        # RESULTS TABS
        # ==================================

        st.subheader("Results")

        tab1, tab2, tab3 = st.tabs(
            [
                f"✅ QE ({len(qe_df)})",
                f"❌ Not QE ({len(not_qe_df)})",
                f"⚠️ Review ({len(review_df)})"
            ]
        )

        # ----------------------------
        # QE
        # ----------------------------

        with tab1:

            st.success(
                f"{len(qe_df)} record(s) classified as QE"
            )

            st.dataframe(
                qe_df,
                hide_index=True,
                use_container_width=True
            )

        # ----------------------------
        # NOT QE
        # ----------------------------

        with tab2:

            st.error(
                f"{len(not_qe_df)} record(s) classified as Not QE"
            )

            st.dataframe(
                not_qe_df,
                hide_index=True,
                use_container_width=True
            )

        # ----------------------------
        # REVIEW
        # ----------------------------

        with tab3:

            st.warning(
                f"{len(review_df)} record(s) require review"
            )

            st.dataframe(
                review_df,
                hide_index=True,
                use_container_width=True
            )

        # ==================================
        # DOWNLOAD
        # ==================================

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
