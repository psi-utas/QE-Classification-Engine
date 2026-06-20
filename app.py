import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(
    page_title="QE Lookup",
    page_icon="🔍",
    layout="wide"
)

# Load Data
@st.cache_data
def load_data():
    return pd.read_excel("QE_Classification_Master_List.xlsx")

df = load_data()

# Title
st.title("🔍 QE Lookup")

# Search Box
search_text = st.text_input(
    "",
    placeholder='Type any payment type or keyword — e.g. "car allowance", "jury duty", "overtime", "parental leave"...'
)

# Search Logic
if search_text:
    results = df[
        df["Name"].str.contains(search_text, case=False, na=False)
    ]

    if not results.empty:
        st.success(f"Found {len(results)} matching result(s)")
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No matches found.")

else:
    st.dataframe(
        df.head(10),
        use_container_width=True,
        hide_index=True
    )
