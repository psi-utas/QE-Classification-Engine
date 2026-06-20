import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

@st.cache_data
def load_master():
    return pd.read_excel("QE_Classification_Master_List.xlsx")

master_df = load_master()

st.title("🔍 QE Lookup")

# =======================================
# Single Search
# =======================================

search_text = st.text_input(
    "",
    placeholder='Type any payment type or keyword — e.g. "car allowance", "jury duty", "overtime", "parental leave"...'
)

if search_text:

    results = master_df[
        master_df["Name"].str.contains(search_text, case=False, na=False)
    ]

    if len(results) > 0:

        for _, row in results.iterrows():

            if row["Type"] == "QE":
                st.success(f"✅ {row['Name']} → QE")

            elif row["Type"] == "Not QE":
                st.error(f"❌ {row['Name']} → Not QE")

            else:
                st.warning(f"⚠️ {row['Name']} → Review")

        st.dataframe(results, use_container_width=True)

    else:
        st.warning("No matches found.")

st.divider()

# =======================================
# Bulk Upload
# =======================================

st.subheader("📤 Bulk QE Classification")

uploaded_file = st.file_uploader(
    "Upload an Excel file containing a Description column",
    type=["xlsx"]
)

if uploaded_file:

    input_df = pd.read_excel(uploaded_file)

    required_col = "Description"

    if required_col not in input_df.columns:
        st.error("Excel file must contain a column named 'Description'")

    else:

        def classify_payment(desc):

            if pd.isna(desc):
                return "Review"

            matches = master_df[
                master_df["Name"].str.contains(
                    str(desc),
                    case=False,
                    na=False,
                    regex=False
                )
            ]

            if len(matches) > 0:
                return matches.iloc[0]["Type"]

            # reverse search
            matches = master_df[
                master_df["Name"].apply(
                    lambda x: str(desc).lower() in str(x).lower()
                )
            ]

            if len(matches) > 0:
                return matches.iloc[0]["Type"]

            return "Review"

        input_df["QE Classification"] = input_df["Description"].apply(
            classify_payment
        )

        st.success(
            f"Processed {len(input_df)} records"
        )

        st.dataframe(
            input_df,
            use_container_width=True
        )

        output_file = "QE_Classified_Output.xlsx"

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            input_df.to_excel(
                writer,
                sheet_name="QE Results",
                index=False
            )

        with open(output_file, "rb") as file:

            st.download_button(
                label="📥 Download Results",
                data=file,
                file_name="QE_Classified_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
