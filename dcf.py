"""
DCF model template — bottom-up, driver-per-cell. Generic and runnable.

This is a GENERIC, company-agnostic skeleton with the proven structure of a
mature model: a PARAMETERS block of tunable value-driver cells read through an
override accessor, and a locked CALCULATION block that builds revenue bottom-up
(segment units x price), walks the cost stack to EBIT -> NOPAT -> FCF, discounts
on a phased WACC, adds a Gordon-Growth terminal value, and bridges enterprise to
equity to a per-share intrinsic value.

The placeholder driver values below are illustrative ONLY — they exist so the
model runs end-to-end and is dcf_score.py-measurable from session one. The
Modeler Agent's job is to REPLACE every placeholder with a real, source-cited
value, and to EXPAND the structure (add segments, cost lines, transition bands,
sub-knobs) until the driver set maps to the business's true mechanics. There is
NO upper cap on parameter count — mature models hold dozens and may pass a
hundred drivers. Density that maps to real business mechanics is the goal.

Conventions the Modeler must preserve (dcf_score.py depends on them):
  - Parameters live between the `=== PARAMETERS` and `=== END PARAMETERS`
    markers, at column 0, organised under `# --- {Functional bucket} ---`
    sub-headers (one band per bucket).
  - Each parameter is a single scalar: `name = number  # note (source)`.
    Plain numbers only — NO digit separators (1_000 will not be parsed).
  - A driver only counts toward `driver_count` if its inline comment contains a
    `data/...` source pointer AND it moves IV when perturbed. Use `data/` for
    primary-source-backed drivers; `wiki/...` citations are rationale, not a
    counted source. Comment text after `#` is capped at 80 chars. REPLACE
    comments each session, never APPEND. Rationale belongs in wiki/drivers/.
  - Per-year arrays are built INSIDE the calculation from stage scalars; never
    store lists as parameters — they break the dcf_score.py per-knob override
    pass that produces the `driver_count` metric.
  - Stage naming: {driver}_{stage} where stage is one of
    base | yr1_3 | yr4_7 | terminal (or analogous explicit-year tags).
  - Sub-knob decomposition: when one rate spans several cited causal drivers,
    split it into 2-5 named sub-knobs that aggregate via an explicit formula in
    CALCULATION (see WACC build-up and cost-inflation example below).

Output contract (preserved across all versions of this file):
    python3 dcf.py --json
must print a single JSON object containing at minimum:
    intrinsic_per_share_usd   (key name is historical; value is in the
                               reporting currency, NOT necessarily USD)
and SHOULD also expose diagnostic keys for downstream agents:
    enterprise_value_bn, equity_value_bn, pv_explicit_fcf_bn, pv_tv_bn,
    terminal_fcf_bn, terminal_value_bn, wacc, terminal_growth,
    year1_revenue_bn, year1_fcf_bn, year_n_revenue_bn, year_n_fcf_bn
Override (used by dcf_score.py, one parameter at a time):
    python3 dcf.py --json --override wacc_terminal=0.09
NOTE: Do NOT include margin_of_safety or any market price comparison. The model
computes intrinsic value only. Price comparison happens outside the loop — the
human does it after the research loop completes.
"""

import argparse
import json
import sys

# ============================================================
# HELPER — override pattern (dcf_score.py uses this)
# ============================================================
_overrides: dict = {}


def p(name: str):
    """Return the override value if set, else the module-level parameter."""
    if name in _overrides:
        return float(_overrides[name])
    return globals()[name]


# ============================================================
# === PARAMETERS — value driver cells (edit here only) ===
# One inline comment per parameter, <=80 chars after '#',
# format:  # <short note> (source)
# NO session numbers, NO prior values, NO reasoning chains.
# Plain numbers only (no 1_000 separators). Rationale -> wiki/drivers/.
# Placeholder values are illustrative — REPLACE with real cited values.
# ============================================================

# --- Horizon flags ---
model_start_yr = 2026     # first explicit fiscal year (structural label)
explicit_yrs   = 8        # explicit forecast horizon, years (data/Filings/...)
terminal_g     = 0.02     # terminal growth rate (data/Filings/... or macro)

# --- Segment A: volume & price drivers ---
seg_a_units_base          = 1000.0  # seg A base-year units, thousands (data/Filings/...)
seg_a_units_growth_yr1_3  = 0.05    # seg A unit growth yrs 1-3 (data/Transcripts/...)
seg_a_units_growth_term   = 0.02    # seg A unit growth terminal (data/Filings/...)
seg_a_price_base          = 100.0   # seg A price per unit, base year (data/Filings/...)
seg_a_price_growth        = 0.02    # seg A price growth per year (data/Filings/...)

# --- Segment B: volume & price drivers ---
seg_b_units_base          = 500.0   # seg B base-year units, thousands (data/Filings/...)
seg_b_units_growth_yr1_3  = 0.04    # seg B unit growth yrs 1-3 (data/Transcripts/...)
seg_b_units_growth_term   = 0.02    # seg B unit growth terminal (data/Filings/...)
seg_b_price_base          = 150.0   # seg B price per unit, base year (data/Filings/...)
seg_b_price_growth        = 0.02    # seg B price growth per year (data/Filings/...)

# --- Cost structure (gross margin glide + opex ratio) ---
gross_margin_base         = 0.30    # gross margin, base year (data/Filings/...)
gross_margin_terminal     = 0.34    # gross margin, terminal (data/Filings/...)
opex_ratio_base           = 0.12    # opex as % of revenue, base year (data/Filings/...)
opex_ratio_terminal       = 0.10    # opex as % of revenue, terminal (data/Filings/...)

# --- Cost-inflation sub-knobs (aggregate into net build-cost drag) ---
input_cost_inflation      = 0.005   # input/material cost inflation, net (data/Transcripts/...)
labour_cost_inflation     = 0.015   # labour cost inflation per year (data/Transcripts/...)
procurement_savings_offset = 0.008  # procurement savings offsetting inflation (data/Filings/...)

# --- One-time transition items (optional band — drags & benefits) ---
transition_cost_yr1       = 15.0    # one-off transition cost, year 1, millions (data/Filings/...)
transition_cost_yr2       = 8.0     # one-off transition cost, year 2, millions (data/Filings/...)
one_time_benefit_total    = 30.0    # cumulative one-off cash benefit, millions (data/Filings/...)
one_time_benefit_yrs      = 3       # years over which the benefit accrues (data/Filings/...)

# --- Tax ---
effective_tax_rate        = 0.25    # cash effective tax rate (data/Filings/...)

# --- D&A ---
da_annual                 = 20.0    # D&A non-cash addback per year, millions (data/Filings/...)

# --- Capex ---
capex_base                = 25.0    # steady-state capex per year, millions (data/Filings/...)
capex_ramp_yrs            = 2       # years of elevated (1.3x) ramp capex (data/Filings/...)

# --- Working capital ---
wc_pct_of_rev_growth      = 0.20    # WC investment as % of revenue growth (data/Filings/...)

# --- WACC sub-knobs (CAPM build-up; phased near-term premium) ---
risk_free_rate            = 0.04    # risk-free rate (data/Filings/... or macro)
equity_risk_premium       = 0.05    # equity risk premium (data/Filings/... or macro)
beta                      = 1.00    # levered/relevered beta (data/Filings/...)
near_term_risk_premium    = 0.01    # extra WACC added in yrs 1-3 (data/Filings/...)

# --- Equity bridge (enterprise -> equity) ---
net_cash                  = 200.0   # net cash (+) or net debt (-), millions (data/Filings/...)
total_debt                = 0.0     # gross debt to deduct, millions (data/Filings/...)
lease_liabilities         = 50.0    # IFRS16/operating lease liabilities, millions (data/Filings/...)
minority_interest         = 0.0     # minority interest to deduct, millions (data/Filings/...)
other_bridge_adj          = 0.0     # other bridge items (pension, JV), millions (data/Filings/...)
diluted_shares            = 100.0   # diluted shares outstanding, millions (data/Filings/...)
# === END PARAMETERS ===


# ============================================================
# CALCULATION — do not edit below this line
# ============================================================


def _seg_units(seg: str, yr_idx: int) -> float:
    """Units for segment 'a'/'b' in year yr_idx (0 = base year)."""
    base = p(f"seg_{seg}_units_base")
    g_near = p(f"seg_{seg}_units_growth_yr1_3")
    g_term = p(f"seg_{seg}_units_growth_term")
    units = base
    for i in range(1, yr_idx + 1):
        units *= (1.0 + (g_near if i <= 3 else g_term))
    return units


def _seg_price(seg: str, yr_idx: int) -> float:
    """Price per unit for segment 'a'/'b' in year yr_idx."""
    return p(f"seg_{seg}_price_base") * ((1.0 + p(f"seg_{seg}_price_growth")) ** yr_idx)


def _revenue_yr(yr_idx: int) -> float:
    """Total revenue (millions) = sum over segments of units(thousands) x price / 1000."""
    rev = 0.0
    for seg in ("a", "b"):
        rev += _seg_units(seg, yr_idx) * _seg_price(seg, yr_idx) / 1000.0
    return rev


def _net_cost_inflation() -> float:
    """Net build-cost inflation drag from cited sub-knobs (illustrative aggregate)."""
    return (p("input_cost_inflation") + p("labour_cost_inflation")
            - p("procurement_savings_offset"))


def _margin_glide(base_name: str, term_name: str, yr_idx: int) -> float:
    """Linear glide from a base-year value to a terminal value over the horizon."""
    base = p(base_name)
    term = p(term_name)
    n = max(int(p("explicit_yrs")) - 1, 1)
    t = min(yr_idx / n, 1.0)
    return base + t * (term - base)


def _ebit_yr(yr_idx: int) -> float:
    """Operating profit (millions): (gross margin - opex ratio - net inflation drag) x rev."""
    rev = _revenue_yr(yr_idx)
    gm = _margin_glide("gross_margin_base", "gross_margin_terminal", yr_idx)
    opex = _margin_glide("opex_ratio_base", "opex_ratio_terminal", yr_idx)
    margin = gm - opex - _net_cost_inflation()
    return rev * margin - _transition_cost_yr(yr_idx)


def _transition_cost_yr(yr_idx: int) -> float:
    """One-off transition cost (millions) for the year (front-loaded band)."""
    if yr_idx == 0:
        return p("transition_cost_yr1")
    if yr_idx == 1:
        return p("transition_cost_yr2")
    return 0.0


def _one_time_benefit_yr(yr_idx: int) -> float:
    """One-off cash benefit (millions) spread evenly over the first N years."""
    n = int(p("one_time_benefit_yrs"))
    if n > 0 and yr_idx < n:
        return p("one_time_benefit_total") / n
    return 0.0


def _tax_yr(yr_idx: int) -> float:
    """Cash tax (millions)."""
    return max(_ebit_yr(yr_idx), 0.0) * p("effective_tax_rate")


def _capex_yr(yr_idx: int) -> float:
    """Capex (millions): elevated 1.3x during the ramp years, then steady-state."""
    if yr_idx < int(p("capex_ramp_yrs")):
        return p("capex_base") * 1.3
    return p("capex_base")


def _wc_change_yr(yr_idx: int) -> float:
    """Working-capital investment (millions) as % of year-on-year revenue growth."""
    if yr_idx == 0:
        return 0.0
    rev_growth = _revenue_yr(yr_idx) - _revenue_yr(yr_idx - 1)
    return max(rev_growth, 0.0) * p("wc_pct_of_rev_growth")


def _fcf_yr(yr_idx: int) -> float:
    """Free cash flow to firm (millions) for year yr_idx."""
    return (_ebit_yr(yr_idx) - _tax_yr(yr_idx) + p("da_annual")
            - _capex_yr(yr_idx) - _wc_change_yr(yr_idx)
            + _one_time_benefit_yr(yr_idx))


def _wacc_terminal() -> float:
    """Terminal WACC via CAPM build-up from cited sub-knobs."""
    return p("risk_free_rate") + p("beta") * p("equity_risk_premium")


def _wacc_near() -> float:
    """Near-term (yrs 1-3) WACC = terminal WACC + near-term risk premium."""
    return _wacc_terminal() + p("near_term_risk_premium")


def main() -> None:
    parser = argparse.ArgumentParser(description="DCF model (template)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--override", action="append", default=[], metavar="NAME=VALUE",
        help="Override a parameter, e.g. --override wacc_terminal=0.09",
    )
    args = parser.parse_args()

    # Apply overrides (dcf_score.py perturbs one parameter at a time)
    for ov in args.override:
        if "=" not in ov:
            print(f"Bad override (expected NAME=VALUE): {ov}", file=sys.stderr)
            sys.exit(1)
        k, v = ov.split("=", 1)
        _overrides[k.strip()] = v.strip()

    wacc_near = _wacc_near()
    wacc_term = _wacc_terminal()
    tg = p("terminal_g")
    n = int(p("explicit_yrs"))

    # --- Explicit period FCF, phased discounting (yrs 1-3 near, yrs 4+ terminal) ---
    explicit_fcfs = [_fcf_yr(i) for i in range(n)]

    def _df(i: int) -> float:
        near_yrs = min(i + 1, 3)
        term_yrs = max(i + 1 - 3, 0)
        return 1.0 / ((1 + wacc_near) ** near_yrs * (1 + wacc_term) ** term_yrs)

    discount_factors = [_df(i) for i in range(n)]
    pv_explicit = sum(f * d for f, d in zip(explicit_fcfs, discount_factors))

    # --- Terminal value (Gordon Growth, discounted at terminal WACC) ---
    terminal_fcf = _fcf_yr(n - 1)
    terminal_fcf_next = terminal_fcf * (1 + tg)
    terminal_value = (terminal_fcf_next / (wacc_term - tg)
                      if (wacc_term - tg) > 0 else 0.0)
    pv_tv = terminal_value / ((1 + wacc_near) ** 3 * (1 + wacc_term) ** (n - 3))

    # --- Enterprise -> equity bridge ---
    enterprise_value = pv_explicit + pv_tv
    equity_value = (enterprise_value
                    + p("net_cash")
                    - p("total_debt")
                    - p("lease_liabilities")
                    - p("minority_interest")
                    + p("other_bridge_adj"))

    shares = p("diluted_shares")
    intrinsic_per_share = equity_value / shares if shares else None

    result = {
        "intrinsic_per_share_usd": round(intrinsic_per_share, 2) if intrinsic_per_share is not None else None,
        "currency": "XXX",  # Modeler: set to the reporting currency
        "enterprise_value_bn": round(enterprise_value / 1000.0, 3),
        "equity_value_bn": round(equity_value / 1000.0, 3),
        "pv_explicit_fcf_bn": round(pv_explicit / 1000.0, 3),
        "pv_tv_bn": round(pv_tv / 1000.0, 3),
        "terminal_fcf_bn": round(terminal_fcf / 1000.0, 3),
        "terminal_value_bn": round(terminal_value / 1000.0, 3),
        "wacc": round(wacc_term, 4),
        "wacc_near": round(wacc_near, 4),
        "terminal_growth": round(tg, 4),
        "year1_revenue_bn": round(_revenue_yr(0) / 1000.0, 3),
        "year1_fcf_bn": round(_fcf_yr(0) / 1000.0, 3),
        "year_n_revenue_bn": round(_revenue_yr(n - 1) / 1000.0, 3),
        "year_n_fcf_bn": round(_fcf_yr(n - 1) / 1000.0, 3),
        "explicit_fcfs_bn": [round(f / 1000.0, 3) for f in explicit_fcfs],
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
