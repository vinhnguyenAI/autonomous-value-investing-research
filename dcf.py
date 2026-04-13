"""
DCF stub for [COMPANY X] ([TICKER]).

This file is intentionally empty. The Modeler Agent will build it from scratch
in Session 1, following the instructions in program.md. Do not hand-edit.

The agent will populate a bottom-up DCF with ~15-30 tunable value drivers,
mapped to real business drivers for the target company. Revenue is built from
segments; costs are broken into meaningful categories; growth is derived, not
assumed. A clear PARAMETERS section (editable) and CALCULATION section (not
editable) will be created.

Output contract (preserved across all versions of this file):
    python3 dcf.py --json
must print a single JSON object containing at minimum:
    intrinsic_per_share_usd
NOTE: Do NOT include margin_of_safety or any market price comparison.
The model computes intrinsic value only. Price comparison happens outside
the model — the human does it after the research loop completes.
"""

import argparse
import json


# === PARAMETERS ===
# Modeler Agent: inject value-driver cells here. Each parameter gets ONE
# ≤80-char citation comment. Rationale goes to wiki/drivers/, not here.
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
