import streamlit as st

st.set_page_config(
    page_title="Insolvency Stress-Testing Engine", page_icon="📈", layout="wide"
)

st.title("Micro-Merchant Cash Runway & Stress Engine")
st.markdown(
    "Institutional-grade liquidity forecasting and market shock simulation for bootstrap founders."
)

st.sidebar.header("Operational Inputs")
starting_cash = st.sidebar.number_input(
    "Current Liquid Cash Balance ($)", value=25000, step=1000
)
monthly_revenue = st.sidebar.number_input(
    "Baseline Monthly Revenue ($)", value=12000, step=500
)
fixed_overhead = st.sidebar.number_input(
    "Monthly Fixed Overhead ($)", value=8000, step=500
)
variable_cost_pct = (
    st.sidebar.slider("Variable Cost Percentage (%)", 0, 100, 40) / 100.0
)
stress_factor = (
    st.sidebar.slider("Market Shock Stress Factor (%)", 0, 50, 20) / 100.0
)

st.write("---")
st.subheader("System Status")
st.info(
    "Sidebar initialized. Ready to render dynamic projection math and stress-test charts."
)
