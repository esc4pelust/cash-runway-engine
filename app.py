import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Insolvency, Working Capital & Diagnostic Engine",
    page_icon="📈",
    layout="wide",
)

st.title("Micro-Merchant Insolvency & Automated Diagnostic Suite")
st.markdown(
    "Institutional-grade cash runway engine featuring macro scenario presets,"
    " CSV statement parsing, dynamic survival playbooks, and tail-risk VaR/CVaR"
    " metrics."
)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("1. Data Intake Method")
intake_mode = st.sidebar.radio(
    "Choose Input Source", ["Manual Sliders", "Upload Financial CSV (P&L)"]
)

# Defaults
starting_cash = 25000
monthly_revenue = 12000
fixed_overhead = 8000
variable_cost_pct = 0.40

if intake_mode == "Upload Financial CSV (P&L)":
  uploaded_file = st.sidebar.file_uploader(
      "Upload CSV (Columns: Month, Revenue, Expenses)"
  )
  if uploaded_file is not None:
    df_user = pd.read_csv(uploaded_file)
    st.sidebar.success("CSV Loaded Successfully!")
    if "Revenue" in df_user.columns:
      monthly_revenue = float(df_user["Revenue"].iloc[-1])
    if "Expenses" in df_user.columns:
      fixed_overhead = float(df_user["Expenses"].iloc[-1])
  else:
    st.sidebar.info(
        "Using default baseline values until a valid CSV is uploaded."
    )

st.sidebar.header("2. Macro Scenario Presets")
scenario = st.sidebar.selectbox(
    "Load Economic Shock Preset",
    [
        "Custom Configuration",
        "Supply Chain Crunch (High Variable Cost)",
        "Inflationary Overhead Spike",
        "Severe Revenue Demand Drop",
    ],
)

if scenario == "Supply Chain Crunch (High Variable Cost)":
  default_shock = 0.15
  default_vol = 0.25
  default_dso = 45
  var_override = 0.65
elif scenario == "Inflationary Overhead Spike":
  default_shock = 0.05
  default_vol = 0.10
  default_dso = 30
  fixed_overhead = fixed_overhead * 1.35
  var_override = variable_cost_pct
elif scenario == "Severe Revenue Demand Drop":
  default_shock = 0.35
  default_vol = 0.30
  default_dso = 60
  var_override = variable_cost_pct
else:
  default_shock = 0.20
  default_vol = 0.15
  default_dso = 30
  var_override = variable_cost_pct

st.sidebar.header("3. Operational & Debt Parameters")
if intake_mode == "Manual Sliders":
  starting_cash = st.sidebar.number_input(
      "Current Liquid Cash ($)", value=starting_cash, step=1000
  )
  monthly_revenue = st.sidebar.number_input(
      "Baseline Monthly Revenue ($)", value=monthly_revenue, step=500
  )
  fixed_overhead = st.sidebar.number_input(
      "Monthly Fixed Overhead ($)", value=fixed_overhead, step=500
  )
  variable_cost_pct = (
      st.sidebar.slider(
          "Variable Cost Percentage (%)", 0, 100, int(var_override * 100)
      )
      / 100.0
  )

dso_days = st.sidebar.slider(
    "Accounts Receivable Lag (DSO Days)", 0, 90, default_dso
)
credit_limit = st.sidebar.number_input(
    "Revolving Credit Line Limit ($)", value=10000, step=1000
)
credit_apr = (
    st.sidebar.slider("Credit Line Interest Rate (APR %)", 0, 36, 14) / 100.0
)

st.sidebar.header("4. Stochastic Monte Carlo Controls")
volatility = (
    st.sidebar.slider("Revenue Volatility (%)", 5, 40, int(default_vol * 100))
    / 100.0
)
shock_factor = (
    st.sidebar.slider("Target Market Shock (%)", 0, 50, int(default_shock * 100))
    / 100.0
)
sims_count = st.sidebar.selectbox(
    "Monte Carlo Iterations", [100, 500, 1000], index=1
)


# --- SIMULATION ENGINE ---
def run_simulation(
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
  collection_factor = 1.0 - (dso / 90.0)

  insolvent_count = 0
  first_insolvency_month = []

  for i in range(sims):
    curr_cash = cash
    debt_balance = 0.0
    hit_zero_month = None

    for m in range(1, months + 1):
      shocked_rev = rev * (1 - shock)
      monthly_shock = np.random.normal(loc=0, scale=vol * shocked_rev)
      realized_rev = max(0, shocked_rev + monthly_shock)
      effective_rev = realized_rev * collection_factor

      net_flow = effective_rev - (fixed + (effective_rev * var_pct))
      net_flow -= debt_balance * monthly_interest_rate
      curr_cash += net_flow

      if curr_cash < 0:
        deficit = abs(curr_cash)
        available_credit = limit - debt_balance
        if deficit <= available_credit:
          debt_balance += deficit
          curr_cash = 0.0
        else:
          debt_balance += available_credit
          curr_cash = -(deficit - available_credit)
          if hit_zero_month is None:
            hit_zero_month = m

      sim_results[i, m] = curr_cash

    if hit_zero_month is not None:
      insolvent_count += 1
      first_insolvency_month.append(hit_zero_month)

  prob_of_default = (insolvent_count / sims) * 100
  avg_insolvency_horizon = (
      np.mean(first_insolvency_month) if first_insolvency_month else 12.0
  )

  ending_liquidity = sim_results[:, -1]
  var_95 = np.percentile(ending_liquidity, 5)
  cvar_95 = np.mean(ending_liquidity[ending_liquidity <= var_95])

  return sim_results, prob_of_default, avg_insolvency_horizon, var_95, cvar_95


sim_data, default_prob, avg_horizon, var_95, cvar_95 = run_simulation(
    starting_cash,
    monthly_revenue,
    fixed_overhead,
    variable_cost_pct,
    dso_days,
    credit_limit,
    credit_apr,
    volatility,
    shock_factor,
    sims_count,
)

# Baseline deterministic calculation
months_list = list(range(0, 13))
baseline_cash = [starting_cash]
curr_b = starting_cash
coll_f = 1.0 - (dso_days / 90.0)
for _ in range(1, 13):
  eff_rev = monthly_revenue * coll_f
  net = eff_rev - (fixed_overhead + (eff_rev * variable_cost_pct))
  curr_b += net
  baseline_cash.append(curr_b)

# --- KPI METRICS DISPLAY ---
st.write("---")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
  st.metric(
      "Probability of Default",
      f"{default_prob:.1f}%",
      delta=(
          "Critical Risk"
          if default_prob > 30
          else ("Manageable" if default_prob > 10 else "Secure")
      ),
      delta_color="inverse",
  )
with c2:
  st.metric(
      "Median Ending Liquidity", f"${np.median(sim_data[:, -1]):,.0f}"
  )
with c3:
  st.metric("95% Tail VaR", f"${var_95:,.0f}")
with c4:
  st.metric("95% Tail CVaR", f"${cvar_95:,.0f}", delta_color="inverse")
with c5:
  st.metric(
      "Expected Default Horizon",
      f"Month {int(avg_horizon)}" if default_prob > 0 else "N/A",
  )

# --- DYNAMIC SURVIVAL PLAYBOOK ---
st.write("---")
st.subheader("Automated Operational Survival Playbook")
if default_prob > 40:
  st.error(
      "**CRITICAL ACTION REQUIRED:** High insolvency probability detected."
      f" Immediate restructuring needed. **Recommendation:** Reduce fixed"
      f" overhead by at least ${int(fixed_overhead*0.25):,.0f}/month or freeze"
      f" non-essential variable expenditures to extend runway past Month"
      f" {int(avg_horizon)}."
  )
elif default_prob > 10:
  st.warning(
      "**MODERATE RISK WARNING:** Vulnerable to market shocks and invoice"
      f" delays. **Recommendation:** Accelerate receivables collection to"
      f" reduce DSO below {max(15, dso_days-15)} days, or negotiate a 30-day"
      " payment extension with primary suppliers."
  )
else:
  st.success(
      "**SECURE LIQUIDITY STATE:** Current capital reserves and credit buffer"
      " successfully absorb simulated volatility parameters. Optimal window"
      " for strategic growth investment."
  )

# --- VISUALIZATIONS ---
st.write("---")
st.subheader("Stochastic Monte Carlo Trajectories")

fig = go.Figure()
for i in range(min(sims_count, 100)):
  fig.add_trace(
      go.Scatter(
          x=months_list,
          y=sim_data[i],
          mode="lines",
          line=dict(width=1, color="rgba(255, 100, 100, 0.12)"),
          showlegend=False,
      )
  )

fig.add_trace(
    go.Scatter(
        x=months_list,
        y=np.median(sim_data, axis=0),
        name="Median Monte Carlo Path",
        line=dict(color="#FF9900", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=months_list,
        y=baseline_cash,
        name="Deterministic Baseline",
        line=dict(color="#00FFFF", width=3, dash="dash"),
    )
)
fig.update_layout(
    xaxis_title="Timeline (Months)", yaxis_title="Liquidity + Credit Buffer ($)"
)
st.plotly_chart(fig, use_container_width=True)

# --- INTERACTIVE SENSITIVITY HEATMAP ---
st.write("---")
st.subheader("Interactive Risk Sensitivity Matrix")
st.markdown(
    "Mapping Probability of Default (%) across varying market shocks and"
    " collection delays."
)

shock_range = np.linspace(0.0, 0.5, 6)
dso_range = np.array([0, 15, 30, 45, 60, 75, 90])
heatmap_matrix = np.zeros((len(dso_range), len(shock_range)))

for d_idx, d in enumerate(dso_range):
  for s_idx, s in enumerate(shock_range):
    _, temp_prob, _, _, _ = run_simulation(
        starting_cash,
        monthly_revenue,
        fixed_overhead,
        variable_cost_pct,
        int(d),
        credit_limit,
        credit_apr,
        volatility,
        s,
        100,
    )
    heatmap_matrix[d_idx, s_idx] = temp_prob

fig_heat = go.Figure(
    data=go.Heatmap(
        z=heatmap_matrix,
        x=[f"{int(s*100)}% Shock" for s in shock_range],
        y=[f"{d} Days DSO" for d in dso_range],
        colorscale="Reds",
        colorbar=dict(title="Default Prob %"),
    )
)
fig_heat.update_layout(
    xaxis_title="Market Shock Severity",
    yaxis_title="Accounts Receivable Lag",
)
st.plotly_chart(fig_heat, use_container_width=True)

# --- EXPORT REPORT BUTTON ---
st.subheader("Institutional Memo Export")
df_summary = pd.DataFrame({
    "Month": months_list,
    "Baseline ($)": baseline_cash,
    "MC 10th Percentile (Stress) ($)": np.percentile(sim_data, 10, axis=0),
    "MC 50th Percentile (Median) ($)": np.median(sim_data, axis=0),
    "MC 90th Percentile (Optimistic) ($)": np.percentile(sim_data, 90, axis=0),
})
csv_data = df_summary.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Executive Stress-Test CSV Report",
    data=csv_data,
    file_name="insolvency_stress_report.csv",
    mime="text/csv",
)
