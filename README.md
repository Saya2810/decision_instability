# decision_instability
A decision-theoretic diagnostic tool for quantifying when financial decisions are ill-posed (mainly stocks).

```
project/
├── data/
│   ├── historical_prices.csv
│   └── download_data.py
│
├── assumptions/
│   └── assumptions.yaml
│
├── engine/
│   └── uncertainty_analysis.jl
│
├── reports/
│   └── decision_validity_report.txt
│
└── plots/
    └── perturbation_overlays.png
```

---


## What do we learn from the perturbation overlay plot?

---

## When should I act – and when should I not?

Use the perturbation overlay plot as a **decision filter**, not a trading signal.  
It answers one concrete question:

> *Is it defensible to act on this historical data, or should I not act at all?*

### You may consider acting if:
- All perturbation curves have **similar shape** (they move together)
- The red uncertainty envelope does **not reverse the trend**
- The verdict is **stable** or **conditionally stable**

In this case:
- Direction may be reliable
- Act with **reduced position size**
- Prefer timing-based decisions over fixed price targets

---

### Act only with strong caution if:
- The red envelope is mostly **parallel but shifted** up or down
- The verdict is **fragile**
- Uncertainty is dominated by window choice or volatility scaling

In this case:
- Direction may still be correct
- Absolute price levels, targets, and leverage are unreliable

---

### You should NOT act if:
- Perturbation curves diverge strongly or cross
- The red envelope invalidates or reverses the original trend
- Overnight gaps or single outliers dominate
- The verdict is **unstable** or **decision unavailable**

In this case:
- The data do not support a defensible decision
- The correct action is **not trading** and gathering more data

---

### One hard rule

> **If your decision would fail under the red envelope, it is not robust.**

The file `plots/perturbation_overlays.png` is the **core diagnostic output** of this project.  
It does **not** attempt to predict prices. Instead, it visualizes **decision instability under uncertainty**.

### How to read the plot

- **Blue bold line (`original`)**  
  The observed historical price path (baseline).

- **Thin colored lines (individual perturbations)**  
  Each line corresponds to *one violated assumption*, for example:
  - `vol_scale = …` → higher/lower volatility than observed  
  - `shift = …` → starting the analysis a few hours later  
  - `friction = … bps` → small execution / transaction costs  

  These lines answer:
  > *“What would the price path look like if this single assumption were slightly wrong?”*

- **Bold red line: `ALL uncertainties (min envelope)`**  
  This is the **aggregate uncertainty path**:
  - At each time, it takes the **worst‑case (minimum) price** across *all* perturbations.
  - It represents the most conservative outcome compatible with the tested uncertainties.

  Conceptually, this is:
  > *“What is the most pessimistic price evolution consistent with all plausible assumption violations?”*

### What this tells us (important)

1. **Decision sensitivity**
   - If the red envelope diverges strongly from the original path,  
     then *small assumption errors lead to large outcome changes*.
   - Any decision based on the original line alone is therefore fragile.

2. **Dominant uncertainty channels**
   - Large separations caused by specific perturbations (e.g. window shifts or volatility scaling)
     indicate *which assumptions matter most*.
   - This is more informative than a single volatility number.

3. **Ill‑posed decisions**
   - If many perturbations fan out quickly, the problem is **ill‑posed**:
     the data do not support a stable conclusion.
   - In such cases, asking “up or down?” is the wrong question.

4. **Worst‑case framing**
   - The red envelope is *not a forecast*.
   - It is a **validity boundary**: a region where decisions remain defensible.
   - This aligns with the project’s goal of **robustness over accuracy**.

### Key takeaway

> **The value of this framework is not predicting returns,  
> but identifying when a financial decision is unreliable because it depends too strongly on hidden assumptions.**

In other words:
- The plot shows *how you can be wrong*,
- why you can be wrong,
- and whether that wrongness matters for your decision.


---

## What calculations does `engine/uncertainty_analysis.jl` perform?

This section documents **all computations performed by the current Julia code**, step by step, in a transparent and reproducible way.

**Important:**  
The goal of this engine is **not price prediction**.  
It evaluates **decision stability / instability** under plausible assumption violations.

---

## 0) Inputs & Configuration

- CSV input: `data/historical_prices.csv`  
  - Generated via Yahoo Finance (`yfinance`)
  - Interval: *hourly*, but **only during market hours** (not 24/7)

- Assumptions file: `assumptions/assumptions.yaml`  
  - Overrides defaults (price column, spread, window lengths, report paths, etc.)

- Key parameters (defaults, possibly overridden by YAML):
  - `price_primary` ∈ {`Close`, `AdjClose`, `Open`, …}
  - `window_lengths` (e.g. `[6, 12, 24]` bars)
  - `spread_bps` (execution cost proxy, in basis points)
  - `VOL_SCALES` (e.g. `[0.5, 1.0, 1.5, 2.0]`)
  - `WINDOW_SHIFTS` (e.g. `[0, 3, 6, 12]` bars)

---

## 1) CSV Loading & Timestamp Parsing

**CSV structure** (typical for Yahoo multi-level headers):
- 3 header rows (column name / ticker / “Datetime”)
- Data starts at row 4
- Columns:  
  `Datetime, AdjClose, Close, High, Low, Open, Volume`

**Parsing:**
- `Datetime` strings are parsed into `ZonedDateTime`
- Formats like  
  `2025-12-22 14:30:00+00:00`  
  are normalized to ISO (`" "` → `"T"`) if needed

---

## 2) Price Series Extraction

From the DataFrame `df`, the engine constructs:

$$
t_i = \text{Datetime}_i
$$

$$
p_i = \text{price\_primary}_i \in \mathbb{R}
$$

---

## 3) Log Returns (Core Quantity)

All risk and perturbation calculations are based on **log returns**:

$$
r_i = \ln\left(\frac{p_{i+1}}{p_i}\right),
\quad i = 1,\dots,n-1
$$

Why log returns?
- Additive over time
- Scale-invariant
- Standard for volatility and regime analysis

---

## 4) Reconstructing Price Paths from Returns

Many perturbations modify returns and then reconstruct prices.

Given modified returns \( r'_i \):

$$
p'_1 = p_1
$$
$$
p'_k = p_1 \cdot \exp\left(\sum_{i=1}^{k-1} r'_i\right)
$$

Implemented in `reconstruct_from_log_returns(p0, r)`.

---

## Uncertainty Channels (Perturbations)

Each perturbation represents a **plausible modeling error**, not a hypothetical extreme scenario.  
Each produces an alternative price path \( p'(t) \).

---

## 5) Perturbation A: Volatility Scaling (Regime Error)

Returns are scaled by a factor \( s \):

$$
r'_i = s \cdot r_i, \quad s \in \texttt{VOL\_SCALES}
$$

Interpretation:  
> “What if the true volatility regime is higher or lower than observed?”

---

## 6) Perturbation B: Window Shift (Start-Time Instability)

The analysis is repeated starting \( h \) bars later.

Steps:
- Drop first \( h \) observations
- Re-anchor reconstructed path to \( p_1 \)

Output:
- First \( h \) points are `NaN`
- Remaining path shows sensitivity to start time

Interpretation:  
> “Would the decision change if I had looked a few hours later?”

---

## 7) Perturbation C: Execution Friction (Transaction Cost Proxy)

A simple robustness stressor (not a microstructure model).

Final price is adjusted by:

$$
\text{cost} =
\left(1 - \frac{\text{spread\_bps}}{10^4}\right)^{\text{trades}}
$$

$$
p'_n = p_n \cdot \text{cost}
$$

Interpretation:  
> “If small transaction costs erase the outcome, the decision is fragile.”

---

## Overlay Plot Construction

---

## 8) Individual Perturbations

- Original price path: **thick line**
- Each perturbation: **thin line**

Each line answers:
> “How wrong could the price path be under this single assumption error?”

---

## 9) Aggregate Uncertainty Envelope (Red Line)

The engine constructs a **worst-case envelope** across all perturbations:

$$
p^{\text{agg}}(t_i) = \min_{k \in \mathcal{P}} p^{(k)}(t_i)
$$

(`NaN` values ignored)

Interpretation:
> “What is the most pessimistic price path consistent with all tested uncertainties?”

This is **not a forecast**.  
It is a **decision-validity boundary**.

---

## Stability & Dominance Metrics

All metrics below are computed on the observed data unless stated otherwise.

---

## 10) Base Volatility (Intraday)

$$
\sigma_{\text{base}} = \text{std}(r)
$$

---

## 11) Window-Length Sensitivity

For each window length \( L \):

$$
\sigma(L) = \text{std}\left(r_{n-L}, \dots, r_{n-1}\right)
$$

Output:
- Dictionary: `L => σ(L)`

Interpretation:
> “Does my risk estimate depend strongly on the chosen window?”

---

## 12) Outlier / Jump Sensitivity

Remove the \( k \) largest absolute returns (default \( k=1 \)):

$$
\sigma_{\text{no\_outlier}} = \text{std}(r \setminus \{\text{largest } |r|\})
$$

Interpretation:
> “Is one extreme event dominating the entire analysis?”

---

## 13) Overnight Gap Risk

For each trading day \( d \):

$$
g_d =
\ln\left(\frac{p_{\text{first of day }d}}
{p_{\text{last of day }d-1}}\right)
$$

$$
\sigma_{\text{overnight}} = \text{std}(g_d)
$$

Interpretation:
> “Is risk dominated by session boundaries rather than intraday movement?”

---

## 14) Optional: Price Definition Sensitivity (Close vs AdjClose)

If both series exist:

$$
\text{vol\_ratio} =
\frac{\sigma(\text{AdjClose})}{\sigma(\text{Close})}
$$

Interpretation:
> “Does the decision depend on accounting / corporate-action conventions?”

---

## 15) Optional: Liquidity Regime Sensitivity (Volume Proxy)

Define low liquidity as the bottom quantile \( q \):

$$
\text{mask}_i =
\left(\text{Volume}_{i+1} \le Q_q(\text{Volume})\right)
$$

$$
\sigma_{\text{lowliq}} = \text{std}(r_i \mid \text{mask}_i)
$$

Interpretation:
> “Is risk dominated by thin trading periods?”

---

## 16) Optional: Market-Factor Dominance (Beta / R²)

If a benchmark column `Close_<BENCH>` exists:

Regression:
$$
r_{\text{asset}} = \alpha + \beta r_{\text{bench}} + \epsilon
$$

$$
\beta = \frac{\operatorname{cov}(r_a, r_b)}{\operatorname{var}(r_b)}
$$


$$
R^2 = 1 - \frac{\sum (r_a - \hat r_a)^2}{\sum (r_a - \bar r_a)^2}
$$


Interpretation:
> “Is the apparent signal actually just market exposure?”

---

## Decision Verdict Logic

---

## 17) Dominance Ranking → Verdict

Each uncertainty channel contributes a **dominance score**, e.g.:

- Window dominance: spread of \( \sigma(L) \) relative to \( \sigma_{\text{base}} \)
- Overnight dominance: \( \sigma_{\text{overnight}} / \sigma_{\text{base}} \)
- Outlier dominance:
$$
\frac{\sigma_{\text{base}} - \sigma_{\text{no\_outlier}}}{\sigma_{\text{base}}}
$$

The strongest channel determines severity:
- `stable`
- `conditionally stable`
- `fragile`
- `unstable`

Severity is mapped to a conservative **decision invalidity probability**:
- stable → 20%
- conditionally stable → 45%
- fragile → 65%
- unstable → 85%

Final output:
- One-sentence verdict
- Explicit statement of decision unreliability

---

## Reporting & Reproducibility

---

## 18) Decision Validity Report

The engine always writes:

reports/decision_validity_report.txt


Containing:
- Decision verdict (one sentence)
- Invalidity probability
- Dominant uncertainty sources
- Numerical summary of all metrics
- Exact assumptions applied

This allows another analyst to **fully reproduce and audit** the decision logic.

---

### Core takeaway

> This framework does not answer *“What will the price do?”*  
> It answers *“Is it intellectually defensible to make a decision based on this data?”*