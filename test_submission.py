"""
KOHLER AI Bathroom Designer - submission validation suite

Run from the project root:
    py test_submission.py

This suite validates the existing recommendation engine and
the layout generator without changing their scoring logic.
"""

import os
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv"
)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )

sys.path.insert(0, str(PROJECT_ROOT))

from src.recommender import (
    recommend_bathroom_top_k,
    calculate_total_cost,
)

from src.layout import create_layout


def check_bundle(bundle, budget, width_ft, depth_ft, label):
    """Validate a complete bathroom recommendation."""
    assert not bundle.empty, f"{label}: recommendation is empty."

    required = {"Toilet", "Faucet", "Shower", "Vanity"}
    actual = set(bundle["category"].astype(str))

    assert required.issubset(actual), (
        f"{label}: missing categories. "
        f"Expected {required}, got {actual}"
    )

    total = float(calculate_total_cost(bundle))

    assert total <= budget, (
        f"{label}: budget exceeded. "
        f"₹{total:,.0f} > ₹{budget:,.0f}"
    )

    max_width = width_ft * 30.48
    max_depth = depth_ft * 30.48

    for _, product in bundle.iterrows():
        product_width = float(product["width_cm"])
        product_depth = float(product["depth_cm"])

        fits_normal = (
            product_width <= max_width
            and product_depth <= max_depth
        )

        fits_rotated = (
            product_depth <= max_width
            and product_width <= max_depth
        )

        assert fits_normal or fits_rotated, (
            f"{label}: {product['category']} dimensions do not fit "
            f"inside the bathroom."
        )

    return total


def check_layout(bundle, width_ft, depth_ft, label):
    """Validate that the layout function generates a figure."""
    fig = create_layout(width_ft, depth_ft, bundle)

    assert fig is not None, f"{label}: layout returned None."

    # A matplotlib figure should contain at least one axes.
    assert len(fig.axes) > 0, f"{label}: layout has no axes."

    return True


def run_case(label, requirements):
    print(f"\\n[{label}]")
    print("Requirements:", requirements)

    results = recommend_bathroom_top_k(
        requirements,
        top_k=3,
    )

    assert results, f"{label}: no recommendations generated."

    print("Recommendation sets:", len(results))

    # Product search: verify requested category and per-product budget.
    if requirements["request_type"] == "product_search":
        for index, result in enumerate(results, start=1):
            assert not result.empty, (
                f"{label} / Result {index}: empty result."
            )

            actual_categories = set(
                result["category"].astype(str)
            )

            expected = set(
                requirements["requested_categories"]
            )

            assert actual_categories.issubset(expected), (
                f"{label}: unexpected category returned. "
                f"Expected {expected}, got {actual_categories}"
            )

            assert (
                result["price"].astype(float)
                <= float(requirements["budget"])
            ).all(), (
                f"{label}: product-level budget exceeded."
            )

            print(
                f"  Result {index}: "
                f"{len(result)} matching products"
            )

        print("  PASS")
        return

    # Complete bathroom: validate the full bundle and layout.
    for index, bundle in enumerate(results, start=1):
        total = check_bundle(
            bundle,
            requirements["budget"],
            requirements["bathroom_width_ft"],
            requirements["bathroom_depth_ft"],
            f"{label} / Option {index}",
        )

        print(
            f"  Option {index}: "
            f"{len(bundle)} products, "
            f"₹{total:,.0f}"
        )

        check_layout(
            bundle,
            requirements["bathroom_width_ft"],
            requirements["bathroom_depth_ft"],
            f"{label} / Option {index}",
        )

    print("  PASS")



def main():
    print("KOHLER AI BATHROOM DESIGNER - SUBMISSION VALIDATION")

    cases = {
        "A - Modern / Water Saving": {
            "request_type": "full_bathroom",
            "requested_categories": [
                "Toilet",
                "Faucet",
                "Shower",
                "Vanity",
            ],
            "budget": 200000,
            "desired_style": "Modern",
            "priority": "Water Saving",
            "bathroom_width_ft": 8,
            "bathroom_depth_ft": 9,
            "missing_information": [],
        },
        "B - Small / Minimalist": {
            "request_type": "full_bathroom",
            "requested_categories": [
                "Toilet",
                "Faucet",
                "Shower",
                "Vanity",
            ],
            "budget": 150000,
            "desired_style": "Minimalist",
            "priority": "Best Overall",
            "bathroom_width_ft": 6,
            "bathroom_depth_ft": 7,
            "missing_information": [],
        },
        "C - Luxury / Large": {
            "request_type": "full_bathroom",
            "requested_categories": [
                "Toilet",
                "Faucet",
                "Shower",
                "Vanity",
            ],
            "budget": 500000,
            "desired_style": "Luxury",
            "priority": "Luxury",
            "bathroom_width_ft": 10,
            "bathroom_depth_ft": 12,
            "missing_information": [],
        },
        "D - Toilet Only / Water Saving": {
            "request_type": "product_search",
            "requested_categories": [
                "Toilet",
            ],
            "budget": 50000,
            "desired_style": "Modern",
            "priority": "Water Saving",
            "bathroom_width_ft": 8,
            "bathroom_depth_ft": 10,
            "missing_information": [],
        },
        "E - Generous Budget / Japanese Zen": {
            "request_type": "full_bathroom",
            "requested_categories": [
                "Toilet",
                "Faucet",
                "Shower",
                "Vanity",
            ],
            "budget": 300000,
            "desired_style": "Japanese Zen",
            "priority": "Best Overall",
            "bathroom_width_ft": 8,
            "bathroom_depth_ft": 10,
            "missing_information": [],
        },
    }

    for label, requirements in cases.items():
        run_case(label, requirements)

    print("\n" + "=" * 68)
    print("ALL CASES PASSED")
  
    print("\nValidated:")
    print("  Done recommendation generation")
    print("  Done product-only search")
    print("  Done complete category coverage")
    print("  Done budget compliance")
    print("  Done catalog dimension compatibility")
    print("  Done 2D layout generation")
    print("  Done multiple bathroom sizes and preferences")


if __name__ == "__main__":
    main()
