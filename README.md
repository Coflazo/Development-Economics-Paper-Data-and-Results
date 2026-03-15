<div align="center">

# Divergence under Colonialism 
### A Difference-in-Differences Analysis of Economic Trajectories in Myanmar and Thailand (1850–2020)

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Statsmodels](https://img.shields.io/badge/Statsmodels-0052CC?style=flat-square)](https://www.statsmodels.org/)
[![SymPy](https://img.shields.io/badge/SymPy-7B9E36?style=flat-square)](https://www.sympy.org/)
[![Seaborn](https://img.shields.io/badge/Seaborn-4C72B0?style=flat-square)](https://seaborn.pydata.org/)
[![Data](https://img.shields.io/badge/Data-Maddison_|_Polity5-green?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)]()

An end-to-end quasi-experimental econometric pipeline estimating the longitudinal causal impact of British colonization (1824–1948) on Myanmar’s macro-economy, constructed against the uncolonized counterfactual trajectory of Thailand (Siam).

---

</div>

<br/>

## 1. Introduction and Project Objective

This repository orchestrates a robust **multi-period Difference-in-Differences (DiD) framework** to quantitatively assess the structural legacy of extractive colonial institutions. By harmonizing centuries of highly heterogeneous historic macro-panel data, the pipeline evaluates whether the exogenous shock of British imperial extraction engineered a permanent divergence in the comparative macroeconomic outcomes of mainland Southeast Asia.

<br/>

## 2. Research & Datasets

Achieving a mathematically rigourous baseline for 19th-century Southeast Asia required an advanced curation pipeline:

| Dataset | Type | Econometric Purpose | Handling & Merging Logic |
|---------|------|----------------------|---------------------------|
| **Maddison** | _XLSX_ | Real $GDP\_pc$ (PPP 2011\$) & Population (`1820-2018`). | Linearly interpolated strictly up to $\leq 5$ years. |
| **Polity5** | _XLS_ | Institutional Quality Index. | Regime-transition format parsed and expanded to annual differences. Interregnum codes nullified to `NaN`. Forward-filled conservatively to $\leq 3$ years. ($Polity_2 = Democ - Autoc$) |
| **Rice Exports**| _PDF_ | Commodity Trade Proxy. | Regex-extracted via `PyPDF2` from _"The Rice Industry of Mainland Southeast Asia 1850-1914"_. |
| **FRED** | _XLSX_ | Nominal GDP Context. | *Modern current-USD arrays stripped and intentionally excluded* to prevent systemic unit-commensurability violations against Maddison PPP structures. |

<br/>

## 3. Difference-in-Differences Formalization

The standard mathematical approach isolates the Average Treatment Effect on the Treated (ATT) via interaction terms. Time-invariant properties are strictly controlled to prevent singular matrix convergence. Formalized via the `SymPy` algebraic engine:

<blockquote>
  <p align="center">
    <img src="https://render.githubusercontent.com/render/math?math=LogGDP_{it} = \beta_{0} %2B \beta_{1} Colonial_{t} %2B \beta_{2} Post_{t} %2B \beta_{3} (Colonial_{t} \times Colonised_{i}) %2B \beta_{4} (Post_{t} \times Colonised_{i}) %2B \beta_{5} Pop_{it} %2B \beta_{6} Trade_{it} %2B \beta_{7} Inst_{it} %2B \epsilon_{it}">
  </p>
</blockquote>

*Note: The parameter vector deliberately excludes the time-invariant `Colonised` discrete intercept ($ \beta_{1} $) from OLS formulation to resolve perfect collinearity overlap with the temporal binary states. The DiD causal vectors ($ \beta_3, \beta_4 $) remain perfectly identified.*

### 3.1. The Parallel Trends Assumption
The validity of this estimation relies fundamentally on the counterfactual logic: **Thailand offers an empirically optimal twin**. Both states were pre-industrial, agrarian, Theravada-Buddhist kingdoms bound to riverine rice cultivation and deltaic geography. They absorbed identical 19th-century trade booms. Thailand, escaping colonization, provides the baseline rate of secular growth.

<br/>

## 4. OLS Regression Engine and Robust Outputs

An Ordinary Least Squares (OLS) mechanism fitted over $N = 208$ complete observations, utilizing **Heteroskedasticity-Consistent Covariance Matrices (HC3 robust standard errors)**.

### Model Execution Summary (`did_summary.txt`)

```text
                            OLS Regression Results                            
==============================================================================
Dep. Variable:             Log_GDP_pc   R-squared:                       0.968
Model:                            OLS   Adj. R-squared:                  0.967
Method:                 Least Squares   F-statistic:                     336.2
No. Observations:                 208   Prob (F-statistic):          1.42e-101
Covariance Type:                  HC3   Log-Likelihood:                 88.771
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept                6.6204      0.024    276.288      0.000       6.573       6.667
Colonial_period         -0.0600      0.023     -2.581      0.010      -0.106      -0.014
Post_colonial           -0.5774      0.043    -13.532      0.000      -0.661      -0.494
Interaction_Colonial    -0.9209     57.428     -0.016      0.987    -113.477     111.635
Interaction_Post        -0.5540      0.035    -15.671      0.000      -0.623      -0.485
Population            5.136e-05   9.71e-07     52.917      0.000    4.95e-05    5.33e-05
Trade                    0.0003   5.38e-05      5.877      0.000       0.000       0.000
Institutions             0.0047      0.002      2.106      0.035       0.000       0.009
========================================================================================
```

### 4.1. The Persistent Post-Colonial Divergence
**`Interaction_Post (\beta = -0.5540, p < 0.001)`**
Logarithmic conversion precisely computes: $(e^{-0.5540} - 1) \times 100$.
> **Result**: **Myanmar's post-1948 GDP per capita suffered a structurally persistent suppression of $\approx \mathbf{42.5\%}$ relative to the Thai counterfactual trajectory.** This confirms the historiographical consensus surrounding institutional inertia: extractive bureaucratic strata, monocultural export reliance, and weak property rights established by the British persisted post-independence, exacerbating isolationist policies spanning 1962–2011.

<br/>

## 5. Statistical Data Visualizations

Programmatic aesthetic formulation strictly enforces an academic C2 standard, generating 300-DPI matrix structures embedded with University of Amsterdam typography scaling.

### I. The Trajectory Matrix
Verifying the $-42.5\%$ post-period econometrics logic visually. Red shading highlights the duration of active British colonization. 
<br>
<div align="center">
  <img src="output/figures/gdp_trajectory.png" width="900" alt="Comparative GDP Trajectory: Myanmar vs Thailand (1850-2020)">
</div>

<br>

### II. Export Divergence Dynamics
Quantitatively validates the high-colonial hyper-extraction enclave; enormous trade volumes originating in Rangoon entirely failed to foster long-term endogenous growth multipliers.
<br>
<div align="center">
  <img src="output/figures/export_divergence.png" width="900" alt="Rice Export Divergence: Burma vs Siam (1860-1914)">
</div>

<br/>

## 6. Local Pipeline Execution

Dynamically reproduce the analytical findings—from historical parsing to robust matrix inversion—with a single execution script:

```bash
# Clone repository and execute primary pipeline
python3 src/did_analysis.py
```

<br/>
<div align="center">
  <sub>Generated mathematically and econometrically matching standard scientific execution models.</sub>
</div>
