"""
DCF stub for [COMPANY X] ([TICKER]).

This file is intentionally empty. The Modeler Agent will build it from scratch
in Session 1, following the instructions in program.md. Do not hand-edit.

The agent will populate a bottom-up DCF with as many tunable value driver
cells as the business genuinely has. There is NO upper cap on parameter
count — mature models typically hold dozens of drivers and may grow well
past a hundred as research uncovers new structure. Density that maps to
real business mechanics is the goal; numerical compactness is not.

Drivers map to real business mechanics for the target company. Revenue is
built segment by segment from units × price (or the segment-appropriate
analogue). Costs are split into the line items management actually steers
(unit cost, headcount cost, input cost, distribution cost, etc.). Growth
is DERIVED from inputs — never assumed via a single top-down rate.

Parameters are organised under sub-header bands by functional bucket:
segment revenue drivers (one band per segment), cost structure lines,
capex schedule, D&A, working capital, tax, WACC (phased where the cost
of capital genuinely changes over the explicit horizon), terminal growth,
capital structure bridge (cash, debt, leases, share count, dilution), and
horizon flags. Optional bands attach where the business actually warrants
them (e.g. contingent liabilities, seasonality overlays, ramp drivers for
new units, regulatory transitions, treasury float).

Stage naming convention: {driver}_{stage} where stage is one of
fy_base | yr1_3 | yr4_7 | terminal (or analogous explicit-year tags).
Per-year arrays are constructed inside CALCULATION from stage scalars;
do not store lists as parameters — they break the bear/bull sed override.

Sub-knob decomposition: when a single growth rate or margin spans multiple
distinct causal drivers cited in research, split it into 2-5 named
sub-knobs that aggregate via an explicit formula in CALCULATION. This is
how the model picks up probability-weighted bets cleanly without forcing
unrelated research into a single parameter.

A clear PARAMETERS section (editable) and CALCULATION section (not
editable) will be created.

Output contract (preserved across all versions of this file):
    python3 dcf.py --json
must print a single JSON object containing at minimum:
    intrinsic_per_share_usd
and SHOULD also expose diagnostic keys for downstream agents:
    enterprise_value_bn, equity_value_bn, pv_explicit_fcf_bn, pv_tv_bn,
    terminal_fcf_bn, terminal_value_bn, wacc, terminal_growth,
    year1_revenue_bn, year1_fcf_bn, year_n_revenue_bn, year_n_fcf_bn
NOTE: Do NOT include margin_of_safety or any market price comparison.
The model computes intrinsic value only. Price comparison happens outside
the model — the human does it after the research loop completes.
"""

import argparse
import json


# === PARAMETERS — value driver cells (edit here only) ===
# Modeler Agent: inject value-driver cells here, organised under
# `# --- {Functional bucket} ---` sub-headers (one band per bucket).
# Each parameter gets ONE ≤80-char citation comment pointing to a
# source under data/ or wiki/drivers/, or to a probabilities.md SXX
# tag. Rationale goes to wiki/drivers/, NOT here. Stage-suffixed
# scalar params only — no per-year lists. REPLACE comments, do not
# APPEND, on every session.
# === END PARAMETERS ===


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {
        "intrinsic_per_share_usd": None,
        "status": "not_yet_built",
    }

    if args.json:
        print(json.dumps(result))
    else:
        print(result)


if __name__ == "__main__":
    main()
