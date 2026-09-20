def explain_recommendation(requirements, bundle):
    """
    Build a factual, user-facing explanation of why a bundle
    satisfies the supplied requirements.

    This function does not change recommendation scoring.
    """

    if bundle is None or bundle.empty:
        return []

    explanations = []

    budget = requirements.get("budget")
    width = requirements.get("bathroom_width_ft")
    depth = requirements.get("bathroom_depth_ft")
    style = requirements.get("desired_style")
    priority = requirements.get("priority")

    total = float(bundle["price"].sum())

    if budget is not None:
        if total <= float(budget):
            explanations.append(
                f"Total cost is ₹{total:,.0f}, within your ₹{float(budget):,.0f} budget."
            )
        else:
            explanations.append(
                f"Total cost is ₹{total:,.0f}, above the ₹{float(budget):,.0f} budget."
            )

    if width is not None and depth is not None:
        explanations.append(
            f"Products were selected after filtering catalog dimensions "
            f"for your {float(width):g} × {float(depth):g} ft bathroom."
        )

    if style:
        explanations.append(
            f"Product ranking includes your {style} style preference."
        )

    if priority == "Water Saving":
        explanations.append(
            "Water efficiency receives higher weight in the recommendation score."
        )
    elif priority == "Luxury":
        explanations.append(
            "Luxury attributes receive higher weight in the recommendation score."
        )
    else:
        explanations.append(
            "The ranking balances style, water efficiency, luxury and compactness."
        )

    categories = [
        str(category)
        for category in bundle["category"].dropna().tolist()
    ]

    if categories:
        explanations.append(
            "Selected categories: " + ", ".join(categories) + "."
        )

    return explanations
