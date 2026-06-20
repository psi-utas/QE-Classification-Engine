# Maruf, Sebgatullah 03013553
# People Systems & Insights

import streamlit as st
import pandas as pd

# version
from streamlit_extras.badges import badge
st.markdown(
    '<img src="https://img.shields.io/badge/version-psi%200.0.0.1-green">',
    unsafe_allow_html=True
)

# GLOBAL UI STYLING
st.markdown("""
<style>
#MainMenu, header, footer {
    visibility: hidden;
}

@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap');

html, body, .stApp, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}

body * {
    font-family: 'Montserrat', sans-serif !important;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

.header-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.header-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0;
}

.header-subtitle {
    font-size: 13px;
    color: grey;
    margin: 0;
}

.logo-container svg {
    height: 40px;
}

hr {
    margin: 6px 0;            
    border: none;
    height: 1px;
    background-color: rgba(255,255,255,0.12);
}

.caption-spacing {
    margin: 4px 0 2px 0;  
    font-size: 12px;
    color: grey;
}

.card {
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
    background-color: rgba(255,255,255,0.05);
}
.card-title {
    font-size: 14px;
}
.card-value {
    font-size: 12px;
    font-weight: 500;
    color: #e42313;
}
</style>
""", unsafe_allow_html=True)

# LOAD SVG LOGO
def load_svg(svg_file):
    with open(svg_file, "r") as f:
        return f.read()

svg_logo = load_svg("utas_logo.svg")

# HEADER 
st.markdown(f"""
<div class="header-container">
    <div>
        <p class="header-title">Gender Pay Gap Simulator</p>
        <p class="header-subtitle">People Systems & Insights</p>
    </div>
    <div class="logo-container">
    <a href="https://www.utas.edu.au/gender-equity" target="_blank">
        {svg_logo}
     </a>
    </div>
</div>
""", unsafe_allow_html=True)

# LOAD DATA
@st.cache_data
def load_data():
    df = pd.read_excel("wgea_data.xlsx")
    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "EmployeeID": "employee_id",
        "Total Remuneration": "salary",
        "Gender": "gender"
    })

    return df

@st.cache_data
def load_salary_plan():
    salary_df = pd.read_excel("salary_plan.xlsx")

    salary_df = salary_df[
        salary_df["SAL_ADMIN_PLAN"].isin(["ACRA", "AUAA", "ELTA"])
    ]

    if "GRADE" in salary_df.columns and "STEP" in salary_df.columns:
        salary_df = salary_df.sort_values(by=["GRADE", "STEP"])

    return salary_df

df = load_data()
salary_df = load_salary_plan()

# CLEAN DATA
df["gender"] = df["gender"].astype(str).str.strip()
df["gender"] = df["gender"].replace({
    "M": "Male",
    "F": "Female",
    "X": "Other"
})

# WORKFORCE SCOPE
st.markdown("<h5>Workforce Scope</h5>", unsafe_allow_html=True)

exclude_casuals = st.checkbox(
    "Exclude Casual employees",
    value=False,
    label_visibility="visible"
)

st.markdown(
    "<small style='color: grey;'>"
    "Default view aligns with official WGEA reporting. "
    "Excluding Casuals is for internal analysis only."
    "</small>",
    unsafe_allow_html=True
)

if exclude_casuals:
    filtered_df = df[df["Employment Type"] != "Casual"]
else:
    filtered_df = df

# CALCULATIONS
def calculate_gpg(data):
    scoped = data[data["gender"].isin(["Male", "Female"])]

    male_avg = scoped[scoped["gender"] == "Male"]["salary"].mean()
    female_avg = scoped[scoped["gender"] == "Female"]["salary"].mean()

    gpg = ((male_avg - female_avg) / male_avg) * 100
    return male_avg, female_avg, gpg

male_avg, female_avg, current_gpg = calculate_gpg(filtered_df)

# Employee counts
male_count = (filtered_df["gender"] == "Male").sum()
female_count = (filtered_df["gender"] == "Female").sum()

total = male_count + female_count

male_pct = (male_count / total) * 100 if total > 0 else 0
female_pct = (female_count / total) * 100 if total > 0 else 0

# CURRENT POSITION
st.markdown("<h5>Organisation Position</h5>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Male Average Salary</div>
        <div class="card-value">${male_avg:,.0f}</div>
    </div>

    <div class="card">
        <div class="card-title">Male Employees</div>
        <div class="card-value">{male_count:,} ({male_pct:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Female Average Salary</div>
        <div class="card-value">${female_avg:,.0f}</div>
    </div>

    <div class="card">
        <div class="card-title">Female Employees</div>
        <div class="card-value">{female_count:,} ({female_pct:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Gender Pay Gap</div>
        <div class="card-value">{current_gpg:.2f}%</div>
    </div>

    <div class="card">
        <div class="card-title">Industry Average (HE)</div>
        <div class="card-value">9.4%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption(f"Total employees analysed: {len(filtered_df):,}")

# SIMULATION SECTION
st.markdown("<h5>Simulation</h5>", unsafe_allow_html=True)
input_mode = st.radio(
    "Input Method",
    ["Use Grade & Step", "Enter TRP Manually"]
)

new_gender = st.selectbox("Gender", ["Male", "Female"])
num_hires = st.slider("Number of hires", 1, 10, 1)

# OPTION 1
if input_mode == "Use Grade & Step":

    grades = salary_df["GRADE_DESC"].dropna().drop_duplicates()
    selected_grade = st.selectbox("Grade", grades)

    steps = salary_df[
        salary_df["GRADE_DESC"] == selected_grade
    ]["STEP_DESC"].dropna().drop_duplicates()

    selected_step = st.selectbox("Step", steps)

    selected_row = salary_df[
        (salary_df["GRADE_DESC"] == selected_grade) &
        (salary_df["STEP_DESC"] == selected_step)
    ]

    if not selected_row.empty:
        monthly_salary = selected_row["MONTHLY_RT"].values[0]
        annual_salary = monthly_salary * 12
        total_salary = annual_salary * 1.17

        st.markdown(f"""
        **Salary Breakdown**
        - Annual: ${annual_salary:,.0f}  
        - Total (incl 17% super): ${total_salary:,.0f}
        """)

        new_salary = total_salary
    else:
        st.warning("Grade/Step not found.")
        new_salary = 0

# OPTION 2
else:
    new_salary = st.number_input(
        "Total Remuneration (TRP)",
        min_value=0.0,
        step=1000.0,
        value=80000.0
    )

# SIMULATION LOGIC
if st.button("Calculate Impact"):

    new_rows = pd.DataFrame({
        "employee_id": [999999] * num_hires,
        "salary": [new_salary] * num_hires,
        "gender": [new_gender] * num_hires
    })

    simulated_df = pd.concat([filtered_df, new_rows], ignore_index=True)
    _, _, new_gpg = calculate_gpg(simulated_df)

    st.markdown("<h5>Impact Analysis</h5>", unsafe_allow_html=True)
    st.write(f"Estimated Gender Pay Gap: **{new_gpg:.3f}%**")

    change = new_gpg - current_gpg
    if change == 0:
        st.info("No material impact on gender pay gap")
    elif change > 0:
        st.error(f"⚠️ Gap widens by {change:.4f}%")
    else:
        st.success(f"✅ Gap improves by {change:.4f}%")

# FOOTER
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 12px; color: grey;'>"
    "Designed & Developed by People Systems & Insights, University of Tasmania"
    "</p>",
    unsafe_allow_html=True
)
