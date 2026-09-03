import pandas as pd
import plotly.express as px
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


def calculate_runway(cash, rev, fixed, var_pct, shock):
  months = list(range(0, 13))
  baseline_cash = [cash]
  stressed_cash = [cash]

  # Baseline projection
  curr_b = cash
  for _ in range(1, 13):
    net = rev - (fixed + (rev * var_pct))
    curr_b += net
    baseline_cash.append(max(0, curr_b))

  # Stressed projection (incorporating market shock)
  stressed_rev = rev * (1 - shock)
  curr_s = cash
  for _ in range(1, 13):
    net_s = stressed_rev - (fixed + (stressed_rev * var_pct))
    curr_s += net_s
    stressed_cash.append(max(0, curr_s))

  df = pd.DataFrame({
      "Month": months,
      "Baseline Cash ($)": baseline_cash,
      "Stressed Cash ($)": stressed_cash,
  })
  return df


df_projection = calculate_runway(
    starting_cash,
    monthly_revenue,
    fixed_overhead,
    variable_cost_pct,
    stress_factor,
)

st.write("---")
st.subheader("12-Month Liquidity Trajectory & Stress Test")

# Render Interactive Plotly Chart
fig = px.line(
    df_projection,
    x="Month",
    y=["Baseline Cash ($)", "Stressed Cash ($)"],
    markers=True,
    labels={"value": "Liquid Capital ($)", "variable": "Projection Model"},
)
fig.update_layout(
    xaxis_title="Timeline (Months)",
    yaxis_title="Cash Balance ($)",
    legend_title="Model State",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Underlying Projection Data")
st.dataframe(df_projection, use_container_width=True)
