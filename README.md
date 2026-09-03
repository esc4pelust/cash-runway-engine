# Micro-Merchant Insolvency & Automated Diagnostic Engine

An institutional-grade, forward-looking cash runway and stress-testing SaaS utility designed to model liquidity insolvency, working capital drag, and stochastic market risk for micro-merchants.

---

## Overview

Traditional accounting software (such as QuickBooks and Xero) excels at backward-looking ledger tracking but remains structurally blind to forward-looking, probabilistic risk. This engine bridges that gap by simulating macroeconomic shocks, working capital delays, and revolving credit facility dynamics to calculate a precise **Probability of Default (%)** over a 12-month horizon. 

---

## Core Features

* **Stochastic Monte Carlo Simulation:** Runs hundreds of randomized iterations factoring in revenue volatility and market shock distributions to map default horizons and median liquidity paths.
* **Working Capital & Debt Drag:** Accounts for Accounts Receivable lag via Days Sales Outstanding (DSO) and automatically models revolving credit line debt-servicing when cash reserves hit zero.
* **Interactive Risk Sensitivity Matrix:** A 2D heatmap visualizing default risk across simultaneous variable axes (Market Shock Severity vs. Accounts Receivable Lag).
* **Automated Operational Survival Playbook:** Generates real-time, context-aware operational recommendations (e.g., overhead cuts, supplier payment terms) based on calculated insolvency risk thresholds.
* **Multi-Modal Data Intake:** Supports both manual slider configurations and automated CSV financial statement parsing.

---

## Quantitative Methodology

### 1. Working Capital Collection Factor
Cash inflows are adjusted dynamically based on invoice collection lag (DSO):
$$\text{Collection Factor} = 1.0 - \left(\frac{\text{DSO}}{90}\right)$$
$$\text{Effective Revenue} = \text{Realized Revenue} \times \text{Collection Factor}$$

### 2. Stochastic Revenue Projection
Monthly revenue incorporates both deterministic market shocks and normally distributed volatility:
$$\text{Shocked Revenue} = \text{Baseline Revenue} \times (1 - \text{Shock Factor})$$
$$\text{Realized Revenue} = \max\left(0, \text{Shocked Revenue} + \mathcal{N}(0, \text{Volatility} \times \text{Shocked Revenue})\right)$$

### 3. Revolving Credit Facility Servicing
When liquid cash drops below zero, the engine assesses available credit limits before triggering insolvency:
$$\text{Deficit} = |\text{Current Cash}|$$
* If $\text{Deficit} \le \text{Available Credit}$, debt increases and cash resets to zero with ongoing monthly interest accrual ($\text{APR} / 12$).
* If $\text{Deficit} > \text{Available Credit}$, the account triggers default status and logs the insolvency horizon month.

---

## Tech Stack

* **Language:** Python 3.9+
* **Framework:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Data Visualization:** Plotly (Scatter plots, confidence bands, heatmaps)

---

## Local Installation & Execution

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/micro-merchant-insolvency-engine.git](https://github.com/your-username/micro-merchant-insolvency-engine.git)
   cd micro-merchant-insolvency-engine
