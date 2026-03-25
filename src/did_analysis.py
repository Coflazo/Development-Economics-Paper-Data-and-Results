"""
working on the myanmar vs thailand DiD analysis (1850-2020)
getting data, doing the math, and making the final plots
"""

import os
import re
import warnings
import urllib.request

import numpy as np
import pandas as pd
import sympy as sp
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import seaborn as sns
from PyPDF2 import PdfReader

warnings.filterwarnings("ignore")

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
FIG = os.path.join(BASE, "output", "figures")
MOD = os.path.join(BASE, "output", "models")

for d in [PROC, FIG, MOD]:
    os.makedirs(d, exist_ok=True)

# --- part 2: getting all the raw data together ---
print("\n[2-A] Extracting Table I-A from PDF …")

pdf_path = os.path.join(RAW, "THE RICE INDUSTRY OF MAINLAND SOUTHEAST ASIA 1850-1914.pdf")
reader = PdfReader(pdf_path)

# Pages 19-20 contain Table I-A
raw_text = ""
for pg_idx in [18, 19]:
    raw_text += reader.pages[pg_idx].extract_text() + "\n"

# pdf parsing was a nightmare with the formatting so just hardcoding the clean table data here

rice_data = {
    "Year": list(range(1860, 1915)),
    "Burma_exports": [
        106, 143, 104, 318, 423, 527, 479, 278, 354, 500,   # 1860-69
        370, 493, 546, 806, 910, 751, 809, 795, 650, 725,    # 1870-79
        816, 941, 1050, 1194, 951, 759, 1078, 1028, 1007, 796,  # 1880-89
        1027, 1381, 1279, 1039, 886, 1282, 1382, 1085, 1118, 1451,  # 1890-99
        1215, 1201, 1360, np.nan, np.nan, np.nan, np.nan, np.nan,  # 1900-07
        np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan    # 1908-14
    ],
    "Siam_exports": [
        64, 83, 44, 114, 160, 3, 99, 122, 139, 180,         # 1860-69
        172, 124, 135, 58, 133, 261, 281, 207, 158, 269,     # 1870-79
        230, 249, 223, 176, 316, 247, 242, 442, 504, 339,    # 1880-89
        539, 253, 238, 887, 588, 548, 536, 667, 618, 510,    # 1890-99
        465, 767, 895, 656, 947, 451, 967, 963, 891, 1028,   # 1900-09
        1067, 1173, 703, 659, 1315                            # 1910-14
    ],
}

# burma footnote says average is 2411, so using that for the missing years
burma_avg_1902_11 = 2411
for i, yr in enumerate(rice_data["Year"]):
    if yr >= 1903 and yr <= 1914 and np.isnan(rice_data["Burma_exports"][i]):
        rice_data["Burma_exports"][i] = burma_avg_1902_11

df_rice = pd.DataFrame(rice_data)
rice_csv = os.path.join(PROC, "historical_rice_exports.csv")
df_rice.to_csv(rice_csv, index=False)
print(f"    ✓ Saved {len(df_rice)} rows → {rice_csv}")
print(df_rice.head(10).to_string(index=False))

# parsing maddison sheet

maddison_path = os.path.join(RAW, "Maddison project Database.xlsx")
df_mad = pd.read_excel(maddison_path, sheet_name="Full data")
df_mad.columns = [c.strip() for c in df_mad.columns]

# Filter for Myanmar and Thailand
df_mad = df_mad[df_mad["countrycode"].isin(["MMR", "THA"])].copy()
df_mad = df_mad.rename(columns={"countrycode": "Country_code", "country": "Country",
                                 "year": "Year", "gdppc": "GDP_pc", "pop": "Population"})
df_mad["Country"] = df_mad["Country_code"].map({"MMR": "Myanmar", "THA": "Thailand"})
df_mad = df_mad[["Year", "Country", "Country_code", "GDP_pc", "Population"]].reset_index(drop=True)

# Population is in thousands in Maddison
print(f"    ✓ Maddison: {len(df_mad)} rows ({df_mad['Year'].min()}–{df_mad['Year'].max()})")
print(f"      Myanmar: {len(df_mad[df_mad['Country']=='Myanmar'])} obs")
print(f"      Thailand: {len(df_mad[df_mad['Country']=='Thailand'])} obs")

# parsing polity sheet for regime types

polity_path = os.path.join(RAW, "p5v2018d.xls")
df_pol = pd.read_excel(polity_path)

# Filter Myanmar (scode=MYA) and Thailand (scode=THI)
df_pol = df_pol[df_pol["scode"].isin(["MYA", "THI"])].copy()

# handle the weird -66/-77 codes by making them nan
for col in ["democ", "autoc"]:
    df_pol[col] = pd.to_numeric(df_pol[col], errors="coerce")
    df_pol.loc[df_pol[col].isin([-66, -77, -88]), col] = np.nan

# the data is in periods, but we need it year by year
annual_rows = []
for _, row in df_pol.iterrows():
    start_yr = int(row["byear"])
    end_yr = int(row["eyear"]) if row["eyear"] < 9000 else 2020
    country = "Myanmar" if row["scode"] == "MYA" else "Thailand"

    for yr in range(start_yr, end_yr):
        democ_val = row["democ"] if not pd.isna(row["democ"]) else np.nan
        autoc_val = row["autoc"] if not pd.isna(row["autoc"]) else np.nan
        polity2 = democ_val - autoc_val if not (pd.isna(democ_val) or pd.isna(autoc_val)) else np.nan
        annual_rows.append({"Year": yr, "Country": country, "polity2": polity2})

df_polity = pd.DataFrame(annual_rows)
# just keep the latest info if there's overlap
print(f"    ✓ Polity5 annual: {len(df_polity)} rows")
print(f"      Myanmar: {df_polity[df_polity['Country']=='Myanmar']['Year'].min()}–{df_polity[df_polity['Country']=='Myanmar']['Year'].max()}")
print(f"      Thailand: {df_polity[df_polity['Country']=='Thailand']['Year'].min()}–{df_polity[df_polity['Country']=='Thailand']['Year'].max()}")

# fred stuff (just keeping it as a reference because it doesnt match maddison's unit types)
print("\n[2-D] Parsing FRED GDP Data (reference column only) …")

fred_tha = pd.read_excel(os.path.join(RAW, "MKTGDPTHA646NWDB.xlsx"), sheet_name="Annual")
fred_tha.columns = ["Date", "GDP_USD"]
fred_tha["Year"] = pd.to_datetime(fred_tha["Date"]).dt.year
fred_tha["Country"] = "Thailand"

fred_mmr = pd.read_excel(os.path.join(RAW, "MKTGDPMMA646NWDB.xlsx"), sheet_name="Annual")
fred_mmr.columns = ["Date", "GDP_USD"]
fred_mmr["Year"] = pd.to_datetime(fred_mmr["Date"]).dt.year
fred_mmr["Country"] = "Myanmar"

df_fred = pd.concat([fred_tha[["Year", "Country", "GDP_USD"]],
                      fred_mmr[["Year", "Country", "GDP_USD"]]], ignore_index=True)
print(f"    ✓ FRED GDP: {len(df_fred)} rows ({df_fred['Year'].min()}–{df_fred['Year'].max()})")


# --- part 3: mix everything together and clean it up ---
print("\n  PHASE 3: Data Engineering, Alignment & Imputation")

# setup basic timeline
years = list(range(1820, 2021))
countries = ["Myanmar", "Thailand"]
timeline = pd.DataFrame([(y, c) for y in years for c in countries],
                         columns=["Year", "Country"])

# join maddison data
df_master = timeline.merge(df_mad[["Year", "Country", "GDP_pc", "Population"]],
                            on=["Year", "Country"], how="left")
print(f"\n  After Maddison merge: {df_master.GDP_pc.notna().sum()} GDP_pc values")

# join polity
df_master = df_master.merge(df_polity[["Year", "Country", "polity2"]],
                             on=["Year", "Country"], how="left")
print(f"  After Polity5 merge: {df_master.polity2.notna().sum()} polity2 values")

# stick fred on there just to have it
df_master = df_master.merge(df_fred[["Year", "Country", "GDP_USD"]],
                             on=["Year", "Country"], how="left")
print(f"  FRED GDP attached as reference: {df_master.GDP_USD.notna().sum()} values (not used in model)")

# format rice data so it joins nicely
rice_mmr = df_rice[["Year", "Burma_exports"]].rename(columns={"Burma_exports": "Trade"})
rice_mmr["Country"] = "Myanmar"
rice_tha = df_rice[["Year", "Siam_exports"]].rename(columns={"Siam_exports": "Trade"})
rice_tha["Country"] = "Thailand"
df_rice_long = pd.concat([rice_mmr, rice_tha], ignore_index=True)

df_master = df_master.merge(df_rice_long, on=["Year", "Country"], how="left")
print(f"  After Rice merge: {df_master.Trade.notna().sum()} Trade values")

# filling missing data carefully so we don't skew the results
print("\n  Imputing missing values …")

for country in countries:
    mask = df_master["Country"] == country
    idx = df_master.loc[mask].index

    # population seems pretty steady so just doing a basic line fill
    df_master.loc[idx, "Population"] = (
        df_master.loc[idx, "Population"].interpolate(method="linear", limit_direction="both")
    )

    # only filling polity stuff forward a few years so we dont accidentally make up a regime change
    df_master.loc[idx, "polity2"] = (
        df_master.loc[idx, "polity2"].ffill(limit=3)
    )

    # fixing gdp gaps but only short ones so we dont jump miles ahead
    df_master.loc[idx, "GDP_pc"] = (
        df_master.loc[idx, "GDP_pc"].interpolate(method="linear", limit=5,
                                                  limit_direction="both")
    )

    df_master.loc[mask & df_master["Trade"].isna(), "Trade"] = 0

print("\n  NOTE: leaving the remaining nans alone, regression will just drop those rows")

# making all the variables we need for the regression
print("\n  Engineering DiD variables …")

# Log GDP per capita
df_master["Log_GDP_pc"] = np.log(df_master["GDP_pc"].clip(lower=1))

# Dummy variables
df_master["Colonised"] = (df_master["Country"] == "Myanmar").astype(int)
df_master["Colonial_period"] = ((df_master["Year"] >= 1824) & (df_master["Year"] <= 1948)).astype(int)
df_master["Post_colonial"] = (df_master["Year"] > 1948).astype(int)

# Interaction terms
df_master["Interaction_Colonial"] = df_master["Colonised"] * df_master["Colonial_period"]
df_master["Interaction_Post"] = df_master["Colonised"] * df_master["Post_colonial"]

# Institutions (polity2)
df_master["Institutions"] = df_master["polity2"]

# Log Population (heavily skewed)
df_master["Log_Population"] = np.log(df_master["Population"].clip(lower=1))

# Save master dataset
master_csv = os.path.join(PROC, "df_master_clean.csv")
df_master.to_csv(master_csv, index=False)
print(f"\n  ✓ Master dataset saved → {master_csv}")
print(f"    Shape: {df_master.shape}")
print(f"    Years: {df_master['Year'].min()}–{df_master['Year'].max()}")
print(f"    Countries: {df_master['Country'].unique()}")
print(f"\n  Sample:\n{df_master[df_master['Year'].isin([1850, 1900, 1950, 2000, 2018])].to_string(index=False)}")


# --- part 4: looking at the math with sympy just for fun ---
print("\n  PHASE 4: Equation")

# gotta define each symbol individually because latex printing breaks otherwise
i, t = sp.symbols("i t")
Log_GDP = sp.Symbol("LogGDP_it")
b0 = sp.Symbol("beta_0")
b1 = sp.Symbol("beta_1")
b2 = sp.Symbol("beta_2")
b3 = sp.Symbol("beta_3")
b4 = sp.Symbol("beta_4")
b5 = sp.Symbol("beta_5")
b6 = sp.Symbol("beta_6")
b7 = sp.Symbol("beta_7")
b8 = sp.Symbol("beta_8")
Colonised_s = sp.Symbol("Colonised_i")
Colonial_s = sp.Symbol("Colonial_t")
Post_s = sp.Symbol("Post_t")
Inter_C = sp.Symbol("ColonisedXColonial")
Inter_P = sp.Symbol("ColonisedXPost")
Pop_s = sp.Symbol("Pop_it")
Trade_s = sp.Symbol("Trade_it")
Inst_s = sp.Symbol("Inst_it")
eps = sp.Symbol("epsilon_it")

# Build equation
rhs = (b0 + b1 * Colonised_s + b2 * Colonial_s +
       b3 * Post_s + b4 * Inter_C + b5 * Inter_P +
       b6 * Pop_s + b7 * Trade_s + b8 * Inst_s + eps)

eq = sp.Eq(Log_GDP, rhs)

print("\n  DiD Model — Pretty Print:\n")
sp.pretty_print(eq)

print("\n\n  DiD Model — LaTeX:\n")
latex_str = sp.latex(eq)
print(f"  $$ {latex_str} $$")

print("\n  Where:")
print("    b4 = colonial effect")
print("    b5 = post-colonial divergence effect")
# --- part 5: running the actual regression ---
print("\n  PHASE 5: Running the model")

# filtering out empty rows so statsmodels doesn't freak out
reg_cols = ["Log_GDP_pc", "Colonised", "Colonial_period", "Post_colonial",
            "Interaction_Colonial", "Interaction_Post", "Population", "Trade",
            "Institutions"]
df_reg = df_master.dropna(subset=reg_cols).copy()

print(f"\n  Regression sample: {len(df_reg)} observations")
print(f"  Myanmar: {len(df_reg[df_reg['Country']=='Myanmar'])}, Thailand: {len(df_reg[df_reg['Country']=='Thailand'])}")

# taking out 'Colonised' variable because it messes up the matrix (it's basically identical to the other variables combined for myanmar everywhere past 1824)
print("\n  ⚠ Note: dropping 'Colonised' since it's collinear with the other stuff")

formula = ("Log_GDP_pc ~ Colonial_period + Post_colonial + "
           "Interaction_Colonial + Interaction_Post + Population + Trade + Institutions")

model = smf.ols(formula, data=df_reg).fit(cov_type="HC3")

print("\n" + "─" * 72)
print(model.summary())
print("─" * 72)

# Extract key interaction terms
print("\n  ══════ KEY INTERACTION TERMS ══════")
for term in ["Interaction_Colonial", "Interaction_Post"]:
    coef = model.params[term]
    se = model.bse[term]
    pval = model.pvalues[term]
    ci = model.conf_int().loc[term]
    sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
    print(f"\n  {term}:")
    print(f"    Coefficient : {coef:+.6f} {sig}")
    print(f"    Std. Error  : {se:.6f}")
    print(f"    p-value     : {pval:.6f}")
    print(f"    95% CI      : [{ci[0]:.6f}, {ci[1]:.6f}]")

# Save regression summary
summary_path = os.path.join(MOD, "did_summary.txt")
with open(summary_path, "w") as f:
    f.write(str(model.summary()))
    f.write("\n\n" + "=" * 72 + "\n")
    f.write("KEY INTERACTION TERMS\n")
    f.write("=" * 72 + "\n")
    for term in ["Interaction_Colonial", "Interaction_Post"]:
        coef = model.params[term]
        se = model.bse[term]
        pval = model.pvalues[term]
        f.write(f"\n{term}:\n")
        f.write(f"  Coefficient : {coef:+.6f}\n")
        f.write(f"  Std. Error  : {se:.6f}\n")
        f.write(f"  p-value     : {pval:.6f}\n")
print(f"\n  ✓ Regression summary saved → {summary_path}")


# --- part 6: graphs ---
print("\n  PHASE 6: Making graphs")

# Download UvA logo
logo_url = "https://upload.wikimedia.org/wikipedia/commons/1/17/Uva%C2%AEmerken_ENG.png"
logo_path = os.path.join(FIG, "uva_logo.png")
if not os.path.exists(logo_path):
    print("  Downloading UvA logo …")
    req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(logo_path, "wb") as f:
        f.write(resp.read())
    print(f"    ✓ Saved → {logo_path}")

# Configure global aesthetics
sns.set_context("paper", font_scale=1.2)
sns.set_style("ticks")
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Georgia"],
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333",
})

def add_logo(fig, alpha=0.15):
    # just stick the uva logo in the corner
    try:
        logo = mpimg.imread(logo_path)
        # Create an inset axes in the lower-right
        ax_logo = fig.add_axes([0.78, 0.02, 0.18, 0.10], anchor="SE")
        ax_logo.imshow(logo, alpha=alpha)
        ax_logo.axis("off")
    except Exception as e:
        print(f"    ⚠ Could not add logo: {e}")

# drawing the gdp graph
print("\n[6-A] Plotting GDP Trajectory …")

fig1, ax1 = plt.subplots(figsize=(12, 6.5))

# Colonial period shading
ax1.axvspan(1824, 1948, alpha=0.12, color="#D32F2F", label="British Colonial Period (1824–1948)",
            zorder=0)

# Plot each country
for country, color, ls in [("Thailand", "#1A5F7A", "-"), ("Myanmar", "#C21010", "--")]:
    subset = df_master[(df_master["Country"] == country) & df_master["Log_GDP_pc"].notna()]
    subset = subset[subset["Year"] >= 1850]
    ax1.plot(subset["Year"], subset["Log_GDP_pc"], color=color, linewidth=2.2,
             linestyle=ls, label=country, zorder=3)

ax1.set_xlabel("Year", fontsize=13, fontweight="medium")
ax1.set_ylabel("Log GDP per Capita (PPP)", fontsize=13, fontweight="medium")
ax1.set_title("Comparative GDP Trajectory: Myanmar vs Thailand (1850–2020)",
              fontsize=15, fontweight="bold", pad=15)
ax1.set_xlim(1850, 2020)
ax1.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=11,
           edgecolor="#cccccc")
ax1.grid(axis="y", alpha=0.3, linestyle="--")
ax1.tick_params(axis="both", which="major", labelsize=11)
sns.despine(ax=ax1)

add_logo(fig1)

gdp_path = os.path.join(FIG, "gdp_trajectory.png")
fig1.savefig(gdp_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig1)
print(f"    ✓ Saved → {gdp_path}")

# drawing the rice graph
print("\n[6-B] Plotting Rice Export Divergence …")

fig2, ax2 = plt.subplots(figsize=(12, 6.5))

ax2.plot(df_rice["Year"], df_rice["Burma_exports"], color="#C21010", linewidth=2.2,
         marker="o", markersize=3.5, label="Burma (Rangoon)", zorder=3)
ax2.plot(df_rice["Year"], df_rice["Siam_exports"], color="#1A5F7A", linewidth=2.2,
         marker="s", markersize=3.5, label="Siam (Bangkok)", zorder=3)

# Fill area between to show divergence
ax2.fill_between(df_rice["Year"], df_rice["Burma_exports"], df_rice["Siam_exports"],
                  alpha=0.08, color="#666666", zorder=1)

# clarify that 1903-1914 Burma exports are table-footnote averages
imputed_mask = df_rice["Year"].between(1903, 1914)
ax2.plot(df_rice.loc[imputed_mask, "Year"], df_rice.loc[imputed_mask, "Burma_exports"],
         color="#C21010", linewidth=2.2, linestyle=":", marker="o", markersize=3.8,
         label="Burma (1903–1914, footnote average)")
ax2.annotate("Burma values for 1903–1914\nuse Table I-A footnote average (2411)",
             xy=(1908, 2411), xytext=(1876, 2600),
             arrowprops=dict(arrowstyle="->", color="#555555", lw=1.0),
             fontsize=10, color="#444444",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#BBBBBB", alpha=0.85))

ax2.set_xlabel("Year", fontsize=13, fontweight="medium")
ax2.set_ylabel("Rice Exports (000 short tons)", fontsize=13, fontweight="medium")
ax2.set_title("Rice Export Divergence: Burma vs Siam (1860–1914)",
              fontsize=15, fontweight="bold", fontfamily="serif", pad=15)
ax2.set_xlim(1860, 1914)
ax2.legend(loc="upper center", ncol=3, frameon=True, framealpha=0.9, fontsize=10,
            edgecolor="#cccccc")
ax2.grid(axis="y", alpha=0.3, linestyle="--")
ax2.tick_params(axis="both", which="major", labelsize=11)
sns.despine(ax=ax2)

add_logo(fig2)

export_path = os.path.join(FIG, "export_divergence.png")
fig2.savefig(export_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig2)
print(f"    ✓ Saved → {export_path}")


# --- part 7: what does it all mean ---
coef_colonial = model.params["Interaction_Colonial"]
pval_colonial = model.pvalues["Interaction_Colonial"]
coef_post = model.params["Interaction_Post"]
pval_post = model.pvalues["Interaction_Post"]

print(f"│  b4 (Interaction_Colonial) = {coef_colonial:+.4f}  (p = {pval_colonial:.4f})")
if pval_colonial < 0.05:
    print("│  looks like the colonial effect was significant!")
else:
    print("│  not really significant during the colonial period alone")

print(f"│  b5 (Interaction_Post) = {coef_post:+.4f}  (p = {pval_post:.4f})")
if pval_post < 0.05:
    print("│  post colonial effect is super significant!")
else:
    print("│  not significant")

print("\n  ALL DONE!")
print(f"""
  Look in these files:
    • {os.path.relpath(rice_csv, BASE)}
    • {os.path.relpath(master_csv, BASE)}
    • {os.path.relpath(summary_path, BASE)}
    • {os.path.relpath(gdp_path, BASE)}
    • {os.path.relpath(export_path, BASE)}
""")
