# decision_instability
A framework for quantifying when financial decisions are ill-posed (mainly Stocks).

```
project/
├── data/
│   ├── historical_prices.csv
│   └── download_data.py
│
├ hooking up assumptions:
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
