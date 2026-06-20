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
# =====================================================
# BULK UPLOAD
# =====================================================

st.divider()

st.subheader("📤 Bulk QE Classification")

example_df = pd.DataFrame({
    "Description": [
        "Parental Leave Half Pay",
        "Family Violence Leave",
        "PILON",
        "Annual Leave",
        "Car Allowance"
    ]
})

st.markdown("### Example File")

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
            "Excel must contain a Description column."
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

        st.subheader("Results")

        st.dataframe(
            result_df,
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

        st.download_button(
            "📥 Download Results",
            output.getvalue(),
            "QE_Classification_Output.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
