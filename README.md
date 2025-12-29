## What do we learn from the perturbation overlay plot?

**Purpose**
- The plot diagnoses whether a financial decision is **robust or ill‑posed**.
- The goal is **decision validity**, not price prediction.

**How the plot is constructed**
- Blue line: observed historical price path
- Thin colored lines: price paths under single‑assumption violations
  - volatility scaling
  - window shifts
  - execution friction
- Thick red line: **worst‑case envelope** (minimum across all perturbations)

**How to read it**
- If curves keep the same shape → dynamics are stable
- If curves diverge or cross → decision is unstable
- If curves are parallel but shifted → level is uncertain, direction may be usable

**When to act**
- ✔ Shapes align, red envelope preserves trend → cautious directional action
- ⚠ Parallel shift only → direction OK, sizing/targets unreliable
- ✘ Curves diverge or envelope reverses trend → do not act

**One hard rule**
> If your decision fails under the red envelope, it is not robust.

**Key takeaway**
- The plot shows **how you can be wrong**, not what will happen.

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
r'_i = s \cdot r_i,\quad s \in \mathrm{VOL\_SCALES}
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