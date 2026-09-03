import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Insolvency & Working Capital Stress Engine",
    page_icon="📈",
    layout="wide",
)

st.title("Micro-Merchant Insolvency, Working Capital & Credit Line Stress Engine")
st.markdown(
    "Institutional liquidity forecasting incorporating Cash Conversion Cycle"
    " (DSO/DPO) drag, revolving debt servicing, and Monte Carlo default"
    " probabilities."
)

st.sidebar.header("1. Core Financial Inputs")
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

st.sidebar.header("2. Working Capital & Debt Parameters")
dso_days = st.sidebar.slider(
    "Accounts Receivable Lag (DSO Days)", 0, 90, 30
)  # Collection delay
credit_limit = st.sidebar.number_input(
    "Revolving Credit Line Limit ($)", value=10000, step=1000
)
credit_apr = (
    st.sidebar.slider("Credit Line Interest Rate (APR %)", 0, 36, 14) / 100.0
)

st.sidebar.header("3. Stochastic & Shock Parameters")
volatility = (
    st.sidebar.slider("Revenue Volatility / Uncertainty (%)", 5, 40, 15) / 100.0
)
shock_factor = (
    st.sidebar.slider("Target Market Shock Drop (%)", 0, 50, 20) / 100.0
)
simulations_count = st.sidebar.selectbox(
    "Monte Carlo Iterations", [100, 500, 1000], index=1
)


def run_advanced_monte_carlo(
    cash,
    rev,
    fixed,
    var_pct,
    dso,
    limit,
    apr,
    vol,
    shock,
    sims,
    months=12,
):
  np.random.seed(42)
  sim_results = np.zeros((sims, months + 1))
  sim_results[:, 0] = cash

  monthly_interest_rate = apr / 12.0
  collection_factor = 1.0 - (
      dso / 90.0
  )  # Simplified cash collection efficiency drag based on DSO

  insolvent_count = 0

  for i in range(sims):
    curr_cash = cash
    debt_balance = 0.0
    hit_zero = False

    for m in range(1, months + 1):
      # Apply market shock and volatility noise
      shocked_rev = rev * (1 - shock)
      monthly_shock = np.random.normal(loc=0, scale=vol * shocked_rev)
      realized_rev = max(0, shocked_rev + monthly_shock)

      # Adjust revenue realization based on DSO collection lag
      effective_rev = realized_rev * collection_factor

      # Costs calculation
      variable_costs = effective_rev * var_pct
      total_outflow = fixed + variable_costs

      # Net cash operations before debt
      net_flow = effective_rev - total_outflow

      # Service existing debt interest if any
      interest_charge = debt_balance * monthly_interest_rate
      net_flow -= interest_charge

      curr_cash += net_flow

      # Credit Line logic if cash goes negative
      if curr_cash < 0:
        deficit = abs(curr_cash)
        available_credit = limit - debt_balance

        if deficit <= available_credit:
          debt_balance += deficit
          curr_cash = 0.0  
        else:
          # Maxed out credit facility -> Hard Insolvency
          debt_balance += available_credit
          curr_cash = - (deficit - available_credit)
          hit_zero = True

      sim_results[i, m] = max(0, curr_cash)

    if hit_zero or curr_cash < 0:
      insolvent_count += 1

  prob_of_default = (insolvent_count / sims) * 100
  return sim_results, prob_of_default


# Execute Advanced Simulation
sim_data, default_prob = run_advanced_monte_carlo(
    starting_cash,
    monthly_revenue,
    fixed_overhead,
    variable_cost_pct,
    dso_days,
    credit_limit,
    credit_apr,
    volatility,
    shock_factor,
    simulations_count,
)

# Deterministic Baseline with Working Capital Drag
months_list = list(range(0, 13))
baseline_cash = [starting_cash]
curr_b = starting_cash
coll_f = 1.0 - (dso_days / 90.0)
for _ in range(1, 13):
  eff_rev = monthly_revenue * coll_f
  net = eff_rev - (fixed_overhead + (eff_rev * variable_cost_pct))
  curr_b += net
  baseline_cash.append(max(0, curr_b))

# KPI Metric Cards
st.write("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      label="Probability of Default (12M)",
      value=f"{default_prob:.1f}%",
      delta=(
          "Critical Risk"
          if default_prob > 30
          else ("Elevated Risk" if default_prob > 10 else "Secure State")
      ),
      delta_color="inverse",
  )
with col2:
  terminal_median = np.median(sim_data[:, -1])
  st.metric(
      label="Median Ending Liquidity", value=f"${terminal_median:,.0f}"
  )
with col3:
  st.metric(
      label="Working Capital Lag (DSO)",
      value=f"{dso_days} Days",
      delta="Invoice Delay",
      delta_color="off",
  )
with col4:
  st.metric(
      label="Credit Facility Capacity",
      value=f"${credit_limit:,.0f}",
      delta=f"APR: {int(credit_apr*100)}%",
      delta_color="off",
  )

st.write("---")
st.subheader("Stochastic Liquidity Trajectories with Credit Facility Buffer")
st.markdown(
    f"Simulating {simulations_count} pathways factoring in a {dso_days}-day"
    f" accounts receivable collection lag and a ${credit_limit:,.0f} revolving"
    " credit safety net."
)

# Plotly Spaghetti Chart
fig = go.Figure()
for i in range(min(sims_count := simulations_count, 100)):
  fig.add_trace(
      go.Scatter(
          x=months_list,
          y=sim_data[i],
          mode="lines",
          line=dict(width=1, color="rgba(255, 100, 100, 0.12)"),
          showlegend=False,
      )
  )

median_path = np.median(sim_data, axis=0)
fig.add_trace(
    go.Scatter(
        x=months_list,
        y=median_path,
        name="Median Monte Carlo Path",
        line=dict(color="#FF9900", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=months_list,
        y=baseline_cash,
        name="Working Capital Baseline",
        line=dict(color="#00FFFF", width=3, dash="dash"),
    )
)

fig.update_layout(
    xaxis_title="Timeline (Months)",
    yaxis_title="Liquid Capital + Credit Buffer ($)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Advanced Risk Distribution Data")
df_summary = pd.DataFrame({
    "Month": months_list,
    "Working Capital Baseline ($)": baseline_cash,
    "MC 10th Percentile (Stress Case) ($)": np.percentile(sim_data, 10, axis=0),
    "MC 50th Percentile (Median) ($)": np.median(sim_data, axis=0),
    "MC 90th Percentile (Optimistic) ($)": np.percentile(sim_data, 90, axis=0),
})
st.dataframe(df_summary, use_container_width=True)
