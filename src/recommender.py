import pandas as pd
from pathlib import Path


    
# LOAD PRODUCT DATA
    

def load_products():

    project_root = Path(__file__).resolve().parent.parent

    data_path = (
        project_root
        / "data"
        / "KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv"
    )

    products = pd.read_csv(data_path)

    return products


    
# HARD CONSTRAINT: BUDGET
    

def filter_products(products, budget):

    return products[
        products["price"].notna()
        & (products["price"] <= budget)
    ].copy()


    
# HARD CONSTRAINT: BATHROOM SIZE
    

def filter_by_size(products, max_width_cm, max_depth_cm):

    return products[
        products["width_cm"].notna()
        & products["depth_cm"].notna()
        & (products["width_cm"] <= max_width_cm)
        & (products["depth_cm"] <= max_depth_cm)
    ].copy()


    
# STYLE SCORE
    

def calculate_style_score(product_style, desired_style):

    # No style preference = neutral score.
    if desired_style is None:
        return 5

    if product_style == desired_style:
        return 10

    if desired_style == "Japanese Zen":

        if product_style == "Organic":
            return 9
        if product_style == "Minimalist":
            return 8
        if product_style == "Modern":
            return 6
        return 5

    if desired_style == "Modern":

        if product_style == "Minimalist":
            return 8
        if product_style == "Luxury":
            return 7
        if product_style == "Organic":
            return 6
        if product_style == "Traditional":
            return 5
        return 5

    if desired_style == "Minimalist":

        if product_style == "Modern":
            return 8
        if product_style == "Organic":
            return 7
        if product_style == "Luxury":
            return 5
        if product_style == "Traditional":
            return 5
        return 5

    if desired_style == "Luxury":

        if product_style == "Modern":
            return 7
        if product_style == "Traditional":
            return 6
        if product_style == "Organic":
            return 5
        if product_style == "Minimalist":
            return 5
        return 5

    return 5


    
# WATER EFFICIENCY SCORE
    

def calculate_water_score(products):

    products = products.copy()

    products["water_score"] = 5.0

    water_categories = [
        "Toilet",
        "Faucet",
        "Shower",
        "Bathtub"
    ]

    for category in water_categories:

        category_mask = (
            (products["category"] == category)
            & products["water_usage"].notna()
        )

        valid_usage = products.loc[
            category_mask,
            "water_usage"
        ]

        if valid_usage.empty:
            continue

        min_usage = valid_usage.min()
        max_usage = valid_usage.max()

        if max_usage == min_usage:

            products.loc[
                category_mask,
                "water_score"
            ] = 10.0

        else:

            products.loc[
                category_mask,
                "water_score"
            ] = (
                10
                - (
                    (
                        products.loc[
                            category_mask,
                            "water_usage"
                        ]
                        - min_usage
                    )
                    / (max_usage - min_usage)
                ) * 9
            )

    return products


    
# COMPACTNESS SCORE
    

def calculate_compact_score(products):

    products = products.copy()

    products["footprint"] = (
        products["width_cm"]
        * products["depth_cm"]
    )

    products["compact_score"] = 5.0

    categories = [
        "Toilet",
        "Faucet",
        "Shower",
        "Bathtub",
        "Vanity"
    ]

    for category in categories:

        category_mask = (
            (products["category"] == category)
            & products["footprint"].notna()
        )

        valid_footprints = products.loc[
            category_mask,
            "footprint"
        ]

        if valid_footprints.empty:
            continue

        min_footprint = valid_footprints.min()
        max_footprint = valid_footprints.max()

        if max_footprint == min_footprint:

            products.loc[
                category_mask,
                "compact_score"
            ] = 10.0

        else:

            products.loc[
                category_mask,
                "compact_score"
            ] = (
                10
                - (
                    (
                        products.loc[
                            category_mask,
                            "footprint"
                        ]
                        - min_footprint
                    )
                    / (max_footprint - min_footprint)
                ) * 9
            )

    return products


    
# FINAL PRODUCT SCORE
    

def calculate_score(product, desired_style, priority):

    style_score = calculate_style_score(
        product["style"],
        desired_style
    )

    water_score = product["water_score"]
    luxury_score = product["luxury_score"]
    compact_score = product["compact_score"]

    if priority == "Water Saving":

        return (
            style_score * 0.4
            + water_score * 0.4
            + compact_score * 0.2
        )

    elif priority == "Luxury":

        return (
            style_score * 0.4
            + luxury_score * 0.4
            + water_score * 0.2
        )

    else:

        return (
            style_score * 0.5
            + water_score * 0.25
            + luxury_score * 0.15
            + compact_score * 0.10
        )


    
# PARETO PRUNING
    

def prune_dominated_states(states):

    states = sorted(
        states,
        key=lambda state: (
            state[0],
            -state[1]
        )
    )

    pruned_states = []
    best_score_seen = -1

    for cost, score, selected_products in states:

        if score > best_score_seen:

            pruned_states.append(
                (
                    cost,
                    score,
                    selected_products
                )
            )

            best_score_seen = score

    return pruned_states


    
# COMPLETE BATHROOM OPTIMIZATION
    

def optimize_bathroom(
    products,
    desired_style,
    priority,
    budget
):

    categories = [
        "Toilet",
        "Faucet",
        "Shower",
        "Vanity"
    ]

    products = products.copy()

    if priority == "Water Saving":

        water_categories = [
            "Toilet",
            "Faucet",
            "Shower",
            "Bathtub"
        ]

        unknown_water = (
            products["category"].isin(water_categories)
            & products["water_usage"].isna()
        )

        products = products[
            ~unknown_water
        ].copy()

    products = calculate_water_score(products)
    products = calculate_compact_score(products)

    products["score"] = products.apply(
        lambda product: calculate_score(
            product,
            desired_style,
            priority
        ),
        axis=1
    )

    states = [
        (0, 0.0, [])
    ]

    for category in categories:

        category_products = products[
            products["category"] == category
        ]

        if category_products.empty:
            return pd.DataFrame()

        candidates = []

        for current_cost, current_score, selected in states:

            for _, product in category_products.iterrows():

                if pd.isna(product["price"]):
                    continue

                product_price = int(product["price"])

                new_cost = current_cost + product_price

                if new_cost > budget:
                    continue

                new_score = (
                    current_score
                    + float(product["score"])
                )

                candidates.append(
                    (
                        new_cost,
                        new_score,
                        selected + [product]
                    )
                )

        if not candidates:
            return pd.DataFrame()

        states = prune_dominated_states(
            candidates
        )

    if not states:
        return pd.DataFrame()

    _, _, best_products = max(
        states,
        key=lambda state: (
            state[1],
            -state[0]
        )
    )

    return pd.DataFrame(best_products)


    
# PRODUCT-SPECIFIC SEARCH
    

def search_products(
    products,
    requested_categories,
    budget,
    desired_style,
    priority,
    top_n=5
):

    products = products.copy()

    # Category constraint
    products = products[
        products["category"].isin(
            requested_categories
        )
    ].copy()

    # Maximum budget constraint
    products = products[
        products["price"].notna()
        & (products["price"] <= budget)
    ].copy()

    # Water-saving constraint
    if priority == "Water Saving":

        water_categories = [
            "Toilet",
            "Faucet",
            "Shower",
            "Bathtub"
        ]

        unknown_water = (
            products["category"].isin(water_categories)
            & products["water_usage"].isna()
        )

        products = products[
            ~unknown_water
        ].copy()

    if products.empty:
        return pd.DataFrame()

    # Internal scoring only.
    # These columns are NOT shown in the UI.
    products = calculate_water_score(products)
    products = calculate_compact_score(products)

    products["score"] = products.apply(
        lambda product: calculate_score(
            product,
            desired_style,
            priority
        ),
        axis=1
    )

    products = products.sort_values(
        by="score",
        ascending=False
    )

    results = []

    for category in requested_categories:

        category_products = products[
            products["category"] == category
        ].head(top_n)

        if not category_products.empty:
            results.append(category_products)

    if not results:
        return pd.DataFrame()

    return pd.concat(
        results,
        ignore_index=True
    )


    
# MAIN RECOMMENDATION FUNCTION
    

def recommend_bathroom(requirements):

    request_type = requirements[
        "request_type"
    ]

    requested_categories = requirements[
        "requested_categories"
    ]

    budget = requirements[
        "budget"
    ]

    desired_style = requirements[
        "desired_style"
    ]

    priority = requirements[
        "priority"
    ]

    bathroom_width_ft = requirements[
        "bathroom_width_ft"
    ]

    bathroom_depth_ft = requirements[
        "bathroom_depth_ft"
    ]

    if budget is None:
        raise ValueError(
            "Budget is required for recommendation."
        )

    products = load_products()

      
    # PRODUCT SEARCH
      

    if request_type == "product_search":

        return search_products(
            products=products,
            requested_categories=requested_categories,
            budget=budget,
            desired_style=desired_style,
            priority=priority
        )

      
    # FULL BATHROOM
      

    if request_type == "full_bathroom":

        if (
            bathroom_width_ft is None
            or bathroom_depth_ft is None
        ):
            raise ValueError(
                "Bathroom dimensions are required "
                "for a full bathroom recommendation."
            )

        max_width_cm = bathroom_width_ft * 30.48
        max_depth_cm = bathroom_depth_ft * 30.48

        products = filter_products(
            products,
            budget
        )

        products = filter_by_size(
            products,
            max_width_cm,
            max_depth_cm
        )

        return optimize_bathroom(
            products,
            desired_style,
            priority,
            budget
        )

    raise ValueError(
        f"Unsupported request type: {request_type}"
    )


    
# TOTAL COST
    

def calculate_total_cost(recommendations):

    if recommendations.empty:
        return 0

    return recommendations["price"].sum()


    
# TOP-K RECOMMENDATIONS
    

def optimize_bathroom_top_k(
    products,
    desired_style,
    priority,
    budget,
    top_k=3
):
    """
    Generate up to top_k valid complete-bathroom combinations.

    The existing scoring, budget filtering, size filtering and
    Pareto pruning logic are preserved. The final valid states
    are ranked by total score and then by lower cost.
    """

    categories = [
        "Toilet",
        "Faucet",
        "Shower",
        "Vanity"
    ]

    top_k = max(1, int(top_k))
    products = products.copy()

    if priority == "Water Saving":

        water_categories = [
            "Toilet",
            "Faucet",
            "Shower",
            "Bathtub"
        ]

        unknown_water = (
            products["category"].isin(water_categories)
            & products["water_usage"].isna()
        )

        products = products[
            ~unknown_water
        ].copy()

    products = calculate_water_score(products)
    products = calculate_compact_score(products)

    products["score"] = products.apply(
        lambda product: calculate_score(
            product,
            desired_style,
            priority
        ),
        axis=1
    )

    states = [
        (0, 0.0, [])
    ]

    for category in categories:

        category_products = products[
            products["category"] == category
        ]

        if category_products.empty:
            return []

        candidates = []

        for current_cost, current_score, selected in states:

            for _, product in category_products.iterrows():

                if pd.isna(product["price"]):
                    continue

                product_price = int(product["price"])
                new_cost = current_cost + product_price

                if new_cost > budget:
                    continue

                new_score = (
                    current_score
                    + float(product["score"])
                )

                candidates.append(
                    (
                        new_cost,
                        new_score,
                        selected + [product]
                    )
                )

        if not candidates:
            return []

        states = prune_dominated_states(candidates)

    # Highest score first, lower cost as tie-breaker.
    ranked_states = sorted(
        states,
        key=lambda state: (
            -state[1],
            state[0]
        )
    )

    results = []

    for cost, score, selected_products in ranked_states[:top_k]:

        bundle = pd.DataFrame(selected_products)

        results.append(bundle)

    return results


def recommend_bathroom_top_k(requirements, top_k=3):
    """
    Public Top-K recommendation API for the Gradio UI.

    Returns:
        list[pd.DataFrame]
    """

    top_k = max(1, int(top_k))

    request_type = requirements[
        "request_type"
    ]

    requested_categories = requirements[
        "requested_categories"
    ]

    budget = requirements[
        "budget"
    ]

    desired_style = requirements[
        "desired_style"
    ]

    priority = requirements[
        "priority"
    ]

    bathroom_width_ft = requirements[
        "bathroom_width_ft"
    ]

    bathroom_depth_ft = requirements[
        "bathroom_depth_ft"
    ]

    if budget is None:
        raise ValueError(
            "Budget is required for recommendation."
        )

    products = load_products()

      
    # SPECIFIC PRODUCT SEARCH
      

    if request_type == "product_search":

        recommendations = search_products(
            products=products,
            requested_categories=requested_categories,
            budget=budget,
            desired_style=desired_style,
            priority=priority,
            top_n=top_k
        )

        if recommendations.empty:
            return []

        # Product search already returns up to top_k products
        # per requested category. Return it as one result set.
        return [recommendations]

      
    # COMPLETE BATHROOM
      

    if request_type == "full_bathroom":

        if (
            bathroom_width_ft is None
            or bathroom_depth_ft is None
        ):
            raise ValueError(
                "Bathroom dimensions are required "
                "for a full bathroom recommendation."
            )

        max_width_cm = bathroom_width_ft * 30.48
        max_depth_cm = bathroom_depth_ft * 30.48

        products = filter_products(
            products,
            budget
        )

        products = filter_by_size(
            products,
            max_width_cm,
            max_depth_cm
        )

        return optimize_bathroom_top_k(
            products=products,
            desired_style=desired_style,
            priority=priority,
            budget=budget,
            top_k=top_k
        )

    raise ValueError(
        f"Unsupported request type: {request_type}"
    )
