"""
dcf_score.py — external auditor for dcf.py.

Computes `driver_count`: the number of parameters in dcf.py that
  (a) carry a `# data/...` source pointer in their inline comment, AND
  (b) move iv_base when perturbed (default × 1.2, or default + 1.0 if zero).

This script is READ-ONLY by all agents. Do NOT edit unless changing the
metric definition. The metric is the ground truth the loop optimises.

Usage:
    python3 dcf_score.py [--quiet]

Output (stdout): JSON {driver_count, iv_base, total_params, active,
no_source, inactive, errors, comment_violations, elapsed_seconds,
audit_per_param: [...]}
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DCF_PATH = Path(__file__).parent / "dcf.py"
PARAM_BLOCK_START = "=== PARAMETERS"
PARAM_BLOCK_END = "=== END PARAMETERS"
PARAM_RE = re.compile(
    r"^([a-z_][a-z_0-9]*)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\s*#\s*(.*)$"
)
INT_LITERAL_RE = re.compile(r"^[a-z_][a-z_0-9]*\s*=\s*-?[0-9]+\s*#")
COMMENT_LEN_CAP = 80
SOURCE_TOKEN = "data/"


def run_dcf(extra_args: list[str]) -> tuple[float | None, str]:
    """Run dcf.py --json with extra_args. Return (iv, error_msg)."""
    try:
        proc = subprocess.run(
            ["python3", str(DCF_PATH), "--json", *extra_args],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout)[:200]
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return None, f"json decode: {e}"
    iv = data.get("intrinsic_per_share_usd")
    if iv is None:
        return None, "missing intrinsic_per_share_usd"
    return float(iv), ""


def extract_params(source: str) -> list[tuple[int, str, float, bool, str]]:
    """Return list of (line_no, name, default, is_int, comment) inside PARAMETERS block."""
    out = []
    in_block = False
    for i, line in enumerate(source.splitlines(), start=1):
        if PARAM_BLOCK_START in line:
            in_block = True
            continue
        if PARAM_BLOCK_END in line:
            break
        if not in_block:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = PARAM_RE.match(line)
        if m:
            name, value, comment = m.group(1), float(m.group(2)), m.group(3).rstrip()
            is_int = bool(INT_LITERAL_RE.match(line))
            out.append((i, name, value, is_int, comment))
    return out


def comment_violations(source: str) -> list[tuple[int, int]]:
    """Return list of (line_no, comment_length) for any comment > COMMENT_LEN_CAP."""
    out = []
    for i, line in enumerate(source.splitlines(), start=1):
        if "#" not in line:
            continue
        comment = line.split("#", 1)[1]
        if len(comment) > COMMENT_LEN_CAP:
            out.append((i, len(comment)))
    return out


def perturb_value(default: float, is_int: bool) -> str:
    """Return CLI-formatted override value that meaningfully differs from default."""
    if is_int:
        return str(int(default) + 1)
    if default == 0.0:
        return "1.0"
    return f"{default * 1.2:.10g}"


def main() -> None:
    parser = argparse.ArgumentParser(description="dcf.py external auditor")
    parser.add_argument("--quiet", action="store_true",
                        help="Omit per-parameter audit detail in JSON output")
    args = parser.parse_args()

    t0 = time.time()
    source = DCF_PATH.read_text()

    iv_base, err = run_dcf([])
    if iv_base is None:
        print(json.dumps({"status": "crash", "stage": "base_run", "error": err}))
        sys.exit(1)

    violations = comment_violations(source)
    params = extract_params(source)

    audit: list[dict] = []
    active = no_source = inactive = errors = 0

    for line_no, name, default, is_int, comment in params:
        entry = {"line": line_no, "name": name, "default": default}
        if SOURCE_TOKEN not in comment:
            entry["status"] = "no_source"
            no_source += 1
            audit.append(entry)
            continue
        new_value = perturb_value(default, is_int)
        iv_new, err = run_dcf([f"--override={name}={new_value}"])
        if iv_new is None:
            entry["status"] = "error"
            entry["error"] = err
            errors += 1
        elif iv_new != iv_base:
            entry["status"] = "active"
            entry["iv_delta"] = round(iv_new - iv_base, 2)
            active += 1
        else:
            entry["status"] = "inactive"
            inactive += 1
        audit.append(entry)

    out = {
        "driver_count": active,
        "iv_base": iv_base,
        "total_params": len(params),
        "active": active,
        "no_source": no_source,
        "inactive": inactive,
        "errors": errors,
        "comment_violations": [{"line": ln, "len": le} for ln, le in violations],
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    if not args.quiet:
        out["audit_per_param"] = audit
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
