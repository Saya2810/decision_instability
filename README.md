## the perturbation overlay plot

"If a plot makes you feel like you learned nothing, but it prevents you from making a bad decision, it did its job."

- Same shape → dynamics are stable  
- Diverging / crossing curves → decision unstable  
- Parallel but shifted curves → level uncertain, direction may still be usable  

**When to act**
- Shapes align, red envelope preserves trend → cautious directional action
- Parallel shift only → direction OK, sizing and targets unreliable
- Envelope reverses trend → do not act

The plot shows **how my decision can fail**, not what will happen.

---

## analysis computation

**Core object**
- Log returns:
$$
r_i = \ln\left(\frac{p_{i+1}}{p_i}\right)
$$

All uncertainty tests operate on perturbations of $r_i$.

---

**Uncertainty channels tested**
- **Volatility regime error**  
$$
r'_i = s \cdot r_i,\quad s \in \mathrm{VOL\_SCALES}
$$

- **Window sensitivity**  
Volatility recomputed on different recent windows \( L \):
$$
\sigma(L) = \operatorname{std}(r_{n-L:\,n})
$$

- **Outlier dominance** (remove top-\(k\) absolute jumps; default \(k=1\))  
$$
r = \ln\!\left(\frac{p_{i+1}}{p_i}\right),\quad
J=\operatorname{arg\,topk}_i |r_i|,\quad
\sigma_{\mathrm{no\_outlier}}=\operatorname{std}\!\bigl(r_{i\notin J}\bigr)
$$

- **Overnight gap risk**
$$
g_d = \ln\left(\frac{p_{\text{open},d}}{p_{\text{close},d-1}}\right),
\quad
\sigma_{\mathrm{overnight}} = \operatorname{std}(g_d)
$$

- **Execution friction**  
Small transaction costs applied as a stressor.
$$
\mathrm{cost}=\left(1-\frac{\mathrm{spread\_bps}}{10^4}\right)^{\mathrm{trades}},\quad
p'_{\mathrm{end}}=p_{\mathrm{end}}\cdot \mathrm{cost}
$$

- **Price-definition sensitivity** (Close vs AdjClose, if both exist)
$$
\mathrm{vol\_ratio}=\frac{\operatorname{std}(r_{\mathrm{AdjClose}})}{\operatorname{std}(r_{\mathrm{Close}})},\quad
\Delta\mu=\operatorname{mean}(r_{\mathrm{AdjClose}})-\operatorname{mean}(r_{\mathrm{Close}})
$$

- **Liquidity regime sensitivity** (Volume proxy; bottom quantile \(q\))
$$
\theta=Q_q(\mathrm{Volume}),\quad
\text{mask}_i=(\mathrm{Volume}_{i+1}\le\theta),\quad
\mathrm{vol\_ratio_{lowliq}}=\frac{\operatorname{std}(r_i\mid \text{mask}_i)}{\operatorname{std}(r)}
$$

- **Market-factor dominance** (benchmark merge required: \(\mathrm{Close}_{\mathrm{BENCH}}\))
$$
\beta=\frac{\operatorname{cov}(r_a,r_b)}{\operatorname{var}(r_b)},\quad
\alpha=\operatorname{mean}(r_a)-\beta\,\operatorname{mean}(r_b),\quad
R^2=1-\frac{\sum (r_a-\hat r_a)^2}{\sum (r_a-\bar r_a)^2}
$$

---

**Aggregation**
- All perturbations operate on \(r_i\) and are reconstructed into a price path:
$$
p'_1=p_1,\quad
p'_{k}=p_1\cdot \exp\!\left(\sum_{i=1}^{k-1} r'_i\right)
$$
- The red curve is the **worst‑case envelope**:
$$
p^{\text{worst}}(t) = \min_{\text{perturbations}} p(t)
$$

---

**Verdict logic**
- I rank uncertainty sources by dominance.
- The strongest one determines whether the decision is:
  - stable
  - conditionally stable
  - fragile
  - unstable
- This maps to a conservative **decision invalidity probability**.
Dominance scores used by the verdict (v0 heuristics):
$$
D_{\mathrm{win}}=\frac{\max_L\sigma(L)-\min_L\sigma(L)}{\sigma_{\mathrm{base}}},\quad
D_{\mathrm{overnight}}=\frac{\sigma_{\mathrm{overnight}}}{\sigma_{\mathrm{base}}},\quad
D_{\mathrm{outlier}}=\frac{\sigma_{\mathrm{base}}-\sigma_{\mathrm{no\_outlier}}}{\sigma_{\mathrm{base}}}
$$
$$
D_{\mathrm{serial}}=1-\frac{n_{\mathrm{eff}}}{n},\quad
D_{\mathrm{regime}}=\frac{\mathrm{CUSUM}}{\mathrm{CUSUM\_threshold}}
$$
---
**Robust volatility (MAD → sigma)**  
$$
\sigma_{\mathrm{MAD}} = c \cdot \mathrm{median}\!\left(\left|r_i-\mathrm{median}(r)\right|\right),\quad c\approx 1.4826
$$

- **Effective sample size (serial dependence penalty)**  
$$
n_{\mathrm{eff}} \approx \frac{n}{1 + 2\sum_{k=1}^{K}\rho_k}
$$

- **Block bootstrap CI for volatility**  
$$
\sigma^{*(b)}=\operatorname{std}(r^{*(b)}),\quad
\mathrm{CI}=\bigl[Q_{\alpha}(\sigma^*),\,Q_{1-\alpha}(\sigma^*)\bigr]
$$

- **CUSUM regime-change proxy**  
$$
S_t=\sum_{i=1}^{t}\frac{r_i}{\sigma},\quad
\mathrm{CUSUM}=\max_t S_t-\min_t S_t
$$
---

**Bottom line**
- This tool does **not** predict prices.
- It tells me whether acting on this data is intellectually defensible.