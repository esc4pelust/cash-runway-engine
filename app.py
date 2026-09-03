import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Insolvency Stress-Testing Engine", page_icon="📈", layout="wide"
)

st.title("Micro-Merchant Cash Runway & Stochastic Stress Engine")
st.markdown(
    "Institutional-grade liquidity forecasting, working capital drag, and Monte"
    " Carlo default probability modeling."
)

st.sidebar.header("Core Financial Inputs")
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

st.sidebar.header("Stochastic & Shock Parameters")
volatility = (
    st.sidebar.slider("Revenue Volatility / Uncertainty (%)", 5, 40, 15) / 100.0
)
shock_factor = (
    st.sidebar.slider("Target Market Shock Drop (%)", 0, 50, 20) / 100.0
)
simulations_count = st.sidebar.selectbox(
    "Monte Carlo Iterations", [100, 500, 1000], index=1
)


def run_monte_carlo(
    cash, rev, fixed, var_pct, vol, shock, sims, months=12
):
  np.random.seed(42)  # Reproducibility
  sim_results = np.zeros((sims, months + 1))
  sim_results[:, 0] = cash

  insolvent_count = 0

  for i in range(sims):
    curr_cash = cash
    hit_zero = False
    for m in range(1, months + 1):
      # Apply stochastic shock with normal distribution noise
      shocked_rev = rev * (1 - shock)
      monthly_shock = np.random.normal(loc=0, scale=vol * shocked_rev)
      realized_rev = max(0, shocked_rev + monthly_shock)

      net_flow = realized_rev - (fixed + (realized_rev * var_pct))
      curr_cash += net_flow

      if curr_cash <= 0:
        curr_cash = 0
        hit_zero = True

      sim_results[i, m] = curr_cash
    if hit_zero:
      insolvent_count += 1

  prob_of_default = (insolvent_count / sims) * 100
  return sim_results, prob_of_default


# Execute Monte Carlo Engine
sim_data, default_prob = run_monte_carlo(
    starting_cash,
    monthly_revenue,
    fixed_overhead,
    variable_cost_pct,
    volatility,
    shock_factor,
    simulations_count,
)

# Baseline deterministic calculation for comparison
months_list = list(range(0, 13))
baseline_cash = [starting_cash]
curr_b = starting_cash
for _ in range(1, 13):
  net = monthly_revenue - (
      fixed_overhead + (monthly_revenue * variable_cost_pct)
  )
  curr_b += net
  baseline_cash.append(max(0, curr_b))

# KPI Metric Cards
st.write("---")
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(
      label="Probability of Insolvency (12M)",
      value=f"{default_prob:.1f}%",
      delta=(
          "High Risk"
          if default_prob > 30
          else ("Moderate Risk" if default_prob > 10 else "Low Risk")
      ),
      delta_color="inverse",
  )
with col2:
  terminal_median = np.median(sim_data[:, -1])
  st.metric(
      label="Median Ending Cash (Stressed)", value=f"${terminal_median:,.0f}"
  )
with col3:
  runway_months = (
      next((i for i, v in enumerate(baseline_cash) if v == 0), 12)
      if baseline_cash[-1] == 0
      else 12
  )
  st.metric(
      label="Baseline Runway Horizon",
      value=f"{runway_months} Months" if runway_months < 12 else "12+ Months",
  )

st.write("---")
st.subheader("Stochastic Monte Carlo Projection Paths")
st.markdown(
    f"Visualizing {simulations_count} randomized economic trajectories under"
    f" {int(volatility*100)}% revenue volatility and {int(shock_factor*100)}%"
    " market shock."
)

# Plotly Monte Carlo Spaghetti Chart
fig = go.Figure()
for i in range(min(sims_count := simulations_count, 100)):  # Plot up to 100 paths for performance
  fig.add_trace(
      go.Scatter(
          x=months_list,
          y=sim_data[i],
          mode="lines",
          line=dict(width=1, color="rgba(100, 150, 250, 0.15)"),
          showlegend=False,
      )
  )

# Add Median Path and Baseline Path
median_path = np.median(sim_data, axis=0)
fig.add_trace(
    go.Scatter(
        x=months_list,
        y=median_path,
        name="Median Monte Carlo Path",
        line=dict(color="orange", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=months_list,
        y=baseline_cash,
        name="Deterministic Baseline",
        line=dict(color="cyan", width=3, dash="dash"),
    )
)

fig.update_layout(
    xaxis_title="Timeline (Months)",
    yaxis_title="Projected Liquidity ($)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Distribution Analysis Data")
df_summary = pd.DataFrame({
    "Month": months_list,
    "Deterministic Baseline ($)": baseline_cash,
    "MC 10th Percentile (Worst Case) ($)": np.percentile(sim_data, 10, axis=0),
    "MC 50th Percentile (Median) ($)": np.median(sim_data, axis=0),
    "MC 90th Percentile (Best Case) ($)": np.percentile(sim_data, 90, axis=0),
})
st.dataframe(df_summary, use_container_width=True)
