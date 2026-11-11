"""Evaluate the local ORACLE MLP against manually labeled log examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.softcomputing.log_classifier import evaluate_labeled_log_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path,
        default=PROJECT_ROOT / "data" / "labeled_logs.csv",
        help="CSV with message,category columns (default: data/labeled_logs.csv)",
    )
    args = parser.parse_args()
    try:
        result = evaluate_labeled_log_dataset(args.dataset)
    except (OSError, ValueError) as error:
        print(f"Cannot evaluate dataset: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
