"""
Repeatable evaluation runner.

Usage:
    python eval/run_eval.py --tag baseline
    python eval/run_eval.py --tag improved

Loads eval/eval_cases.json, runs each case through the SAME answer()
function the real app uses, and writes the full raw record (query,
retrieved chunks, distances, final answer, citations, refusal flag)
to eval/results/<tag>.json.

What this script scores automatically:
  - refusal correctness (expect_refusal vs actual refused flag)

What it deliberately does NOT auto-score, because it needs a human:
  - faithfulness (does the cited timestamp actually support the claim?)
  - overall usefulness of the explanation

Open eval/results/<tag>.json, read the raw answer + citations for each
case, spot-check the cited timestamps against the actual audio, and
record your findings in EVAL.md. Don't just report the refusal-accuracy
number as if it were the whole evaluation -- it isn't.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from rag import answer  # noqa: E402

CASES_PATH = Path(__file__).parent / "eval_cases.json"
RESULTS_DIR = Path(__file__).parent / "results"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True, help="e.g. baseline, improved")
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text())
    results = {}
    session_history = {}  # case_id -> [{"role":..,"content":..}, ...] for followups

    correct_refusals = 0
    total = 0

    for case in cases:
        history = None
        if case.get("requires_history"):
            history = session_history.get(case["requires_history"])

        record = answer(case["query"], chat_history=history)
        matched_expectation = record["refused"] == case["expect_refusal"]

        results[case["id"]] = {
            "type": case["type"],
            "query": case["query"],
            "expect_refusal": case["expect_refusal"],
            "actual_refused": record["refused"],
            "refusal_correct": matched_expectation,
            "answer": record["answer"],
            "citations": record["citations"],
            "retrieved_debug": record["retrieved"],
        }

        # Stash this turn's history so a dependent follow-up case can use it.
        session_history[case["id"]] = [
            {"role": "user", "content": case["query"]},
            {"role": "assistant", "content": record["answer"]},
        ]

        total += 1
        if matched_expectation:
            correct_refusals += 1

        print(f"[{case['id']}] refusal_correct={matched_expectation} refused={record['refused']}")

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{args.tag}.json"
    out_path.write_text(json.dumps(results, indent=2))

    print(f"\nRefusal accuracy: {correct_refusals}/{total}")
    print(f"Raw results written to {out_path}")
    print("Now manually spot-check faithfulness -- this script can't do that part for you.")


if __name__ == "__main__":
    main()
