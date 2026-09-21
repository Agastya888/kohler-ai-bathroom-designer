import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from src.recommender import (
    recommend_bathroom_top_k,
    calculate_total_cost
)

from src.requirement_extractor import extract_requirements
from src.layout import create_layout


  
# INDIAN CURRENCY FORMATTER
  

def format_indian_currency(value):
    """Format a number using the Indian numbering system."""

    if value is None:
        return "Not provided"

    value = float(value)
    sign = "-" if value < 0 else ""
    number = str(abs(int(round(value))))

    if len(number) <= 3:
        formatted = number
    else:
        last_three = number[-3:]
        remaining = number[:-3]
        groups = []

        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        if remaining:
            groups.insert(0, remaining)

        formatted = ",".join(groups) + "," + last_three

    return f"₹{sign}{formatted}"


  
# EMPTY TABLE
  

def empty_table():
    return pd.DataFrame(
        columns=[
            "Category",
            "Product Name",
            "Price"
        ]
    )


  
# FORMAT REQUIREMENTS
  

def format_requirements(requirements):

    request_type = requirements["request_type"]
    categories = ", ".join(
        requirements["requested_categories"]
    )

    budget = requirements["budget"]
    style = requirements["desired_style"]
    priority = requirements["priority"]

    width = requirements["bathroom_width_ft"]
    depth = requirements["bathroom_depth_ft"]

    request_text = (
        "Complete Bathroom Design"
        if request_type == "full_bathroom"
        else "Find Specific Products"
    )

    budget_text = format_indian_currency(budget)

    style_text = (
        style
        if style is not None
        else "No preference"
    )

    if width is not None and depth is not None:
        size_text = f"{width:g} ft × {depth:g} ft"
    else:
        size_text = "Not required"

    return f"""
<div class="profile-card">

<div class="profile-grid">

<div class="profile-item">
<span class="profile-label">REQUEST</span>
<span class="profile-value">{request_text}</span>
</div>

<div class="profile-item">
<span class="profile-label">PRODUCTS</span>
<span class="profile-value">{categories}</span>
</div>

<div class="profile-item">
<span class="profile-label">BUDGET</span>
<span class="profile-value">{budget_text}</span>
</div>

<div class="profile-item">
<span class="profile-label">STYLE</span>
<span class="profile-value">{style_text}</span>
</div>

<div class="profile-item">
<span class="profile-label">PRIORITY</span>
<span class="profile-value">{priority}</span>
</div>

<div class="profile-item">
<span class="profile-label">BATHROOM SIZE</span>
<span class="profile-value">{size_text}</span>
</div>

</div>

</div>
"""


  
# BUILD REQUIREMENTS FROM CUSTOM FORM
  

def build_custom_requirements(
    design_type,
    budget,
    width,
    depth,
    style,
    priority,
    toilet,
    faucet,
    shower,
    vanity
):

    if budget is None or budget <= 0:
        return None, "Please enter a valid budget."

    desired_style = (
        None
        if style == "No preference"
        else style
    )

      
    # COMPLETE BATHROOM
      

    if design_type == "Complete Bathroom":

        if width is None or depth is None:
            return (
                None,
                "Please enter both bathroom width and depth."
            )

        if width <= 0 or depth <= 0:
            return (
                None,
                "Bathroom dimensions must be greater than zero."
            )

        return {
            "request_type": "full_bathroom",
            "requested_categories": [
                "Toilet",
                "Faucet",
                "Shower",
                "Vanity"
            ],
            "budget": budget,
            "desired_style": desired_style,
            "priority": priority,
            "bathroom_width_ft": width,
            "bathroom_depth_ft": depth,
            "missing_information": []
        }, None

      
    # SPECIFIC PRODUCT SEARCH
      

    categories = []

    if toilet:
        categories.append("Toilet")

    if faucet:
        categories.append("Faucet")

    if shower:
        categories.append("Shower")

    if vanity:
        categories.append("Vanity")

    if not categories:
        return (
            None,
            "Please select at least one product category."
        )

    return {
        "request_type": "product_search",
        "requested_categories": categories,
        "budget": budget,
        "desired_style": desired_style,
        "priority": priority,
        "bathroom_width_ft": None,
        "bathroom_depth_ft": None,
        "missing_information": []
    }, None


  
# FORMAT ONE RESULT FOR THE CUSTOMER
  

def format_result_table(recommendations):

    display_columns = [
        "category",
        "name",
        "price"
    ]

    missing = [
        column
        for column in display_columns
        if column not in recommendations.columns
    ]

    if missing:
        raise ValueError(
            f"Unexpected recommender columns: {missing}"
        )

    results = recommendations[
        display_columns
    ].copy()

    results = results.rename(
        columns={
            "category": "Category",
            "name": "Product Name",
            "price": "Price"
        }
    )

    results["Price"] = results["Price"].apply(
        format_indian_currency
    )

    return results


  
# PREPARE TOP-K RESULTS
  

def prepare_results(requirements, top_k):

    try:

        recommendation_sets = (
            recommend_bathroom_top_k(
                requirements,
                top_k=top_k
            )
        )

    except Exception as error:

        return {
            "status": (
                "### We couldn’t find a suitable recommendation\n\n"
                f"{error}"
            ),
            "table": empty_table(),
            "total": "",
            "choices": [],
            "state": [],
            "selector_visible": False
        }

    if not recommendation_sets:

        if requirements["request_type"] == "product_search":

            message = (
                "### No exact match found\n\n"
                "No products in the selected category fit "
                "within the specified budget."
            )

        else:

            message = (
                "### No complete bathroom combination found\n\n"
                "Try increasing your budget or providing a "
                "larger bathroom size."
            )

        return {
            "status": message,
            "table": empty_table(),
            "total": "",
            "choices": [],
            "state": [],
            "selector_visible": False
        }

      
    # Product search
      

    if requirements["request_type"] == "product_search":

        recommendations = recommendation_sets[0]

        table = format_result_table(
            recommendations
        )

        total_html = """
<div class="total-card">
<span class="total-label">PRODUCT OPTIONS</span>
<span class="total-sub">
Showing the highest-ranked options that satisfy the selected budget.
</span>
</div>
"""

        return {
            "status": (
                "### Product recommendations generated"
            ),
            "table": table,
            "total": total_html,
            "choices": [],
            "state": [],
            "selector_visible": False
        }

      
    # Complete bathroom
      

    state = []
    choices = []

    for index, recommendations in enumerate(
        recommendation_sets,
        start=1
    ):

        total = calculate_total_cost(
            recommendations
        )

        budget = requirements["budget"]
        remaining = budget - total

        if remaining >= 0:
            budget_text = (
                f"Within budget by {format_indian_currency(remaining)}"
            )
        else:
            budget_text = (
                f"{format_indian_currency(abs(remaining))} over budget"
            )

        table = format_result_table(
            recommendations
        )

        total_html = f"""
<div class="total-card">
<span class="total-label">TOTAL PROJECT COST</span>
<span class="total-value">{format_indian_currency(total)}</span>
<span class="total-sub">{budget_text}</span>
</div>
"""

        state.append(
            {
                "table": table,
                "total": total_html,
                "recommendations": recommendations
            }
        )

        choices.append(
            f"Recommendation {index}"
        )

    return {
        "status": (
            f"### {len(state)} bathroom recommendation"
            f"{'s' if len(state) != 1 else ''} generated"
        ),
        "table": state[0]["table"],
        "total": state[0]["total"],
        "choices": choices,
        "state": state,
        "selector_visible": len(state) > 1
    }


  
# NATURAL LANGUAGE MODE
  

def generate_from_text(
    user_input,
    top_k
):

    if not user_input or not user_input.strip():

        return (
            "Please describe your requirements.",
            "",
            empty_table(),
            "",
            gr.update(
                choices=[],
                value=None,
                visible=False
            ),
            [],
            {}
        )

    try:

        requirements = extract_requirements(
            user_input
        )

    except Exception as error:

        return (
            "### We couldn’t understand the request\n\n"
            + str(error),
            "",
            empty_table(),
            "",
            gr.update(
                choices=[],
                value=None,
                visible=False
            ),
            [],
            {}
        )

    profile = format_requirements(
        requirements
    )

    missing = requirements.get(
        "missing_information",
        []
    )

    if missing:

        labels = []

        for item in missing:

            if item == "budget":
                labels.append("Budget")

            elif item == "bathroom dimensions":
                labels.append(
                    "Bathroom dimensions"
                )

        message = (
            "### A little more information is needed\n\n"
            + "\n".join(
                f"- {item}"
                for item in labels
            )
            + "\n\nPlease provide the missing information "
              "before generating recommendations."
        )

        return (
            message,
            profile,
            empty_table(),
            "",
            gr.update(
                choices=[],
                value=None,
                visible=False
            ),
            [],
            {}
        )

    result = prepare_results(
        requirements,
        int(top_k)
    )

    selector_update = gr.update(
        choices=result["choices"],
        value=(
            result["choices"][0]
            if result["choices"]
            else None
        ),
        visible=result["selector_visible"]
    )

    return (
        result["status"],
        profile,
        result["table"],
        result["total"],
        selector_update,
        result["state"],
        requirements
    )


  
# CUSTOM FORM MODE
  

def generate_from_form(
    design_type,
    budget,
    width,
    depth,
    style,
    priority,
    toilet,
    faucet,
    shower,
    vanity,
    top_k
):

    requirements, error = build_custom_requirements(
        design_type,
        budget,
        width,
        depth,
        style,
        priority,
        toilet,
        faucet,
        shower,
        vanity
    )

    if error:

        return (
            f"### {error}",
            "",
            empty_table(),
            "",
            gr.update(
                choices=[],
                value=None,
                visible=False
            ),
            [],
            {}
        )

    profile = format_requirements(
        requirements
    )

    result = prepare_results(
        requirements,
        int(top_k)
    )

    selector_update = gr.update(
        choices=result["choices"],
        value=(
            result["choices"][0]
            if result["choices"]
            else None
        ),
        visible=result["selector_visible"]
    )

    return (
        result["status"],
        profile,
        result["table"],
        result["total"],
        selector_update,
        result["state"],
        requirements
    )


  
# CHANGE SELECTED RECOMMENDATION
  

def show_selected_recommendation(
    selected,
    state
):

    if not state or not selected:
        return empty_table(), ""

    try:
        index = int(
            selected.split()[-1]
        ) - 1
    except (ValueError, IndexError):
        return empty_table(), ""

    if index < 0 or index >= len(state):
        return empty_table(), ""

    result = state[index]

    return (
        result["table"],
        result["total"]
    )



  
# GENERATE 2D BATHROOM LAYOUT
  

def update_layout_button(requirements):
    """Show the layout button only after a successful complete-bathroom recommendation."""
    if (
        isinstance(requirements, dict)
        and requirements.get("request_type") == "full_bathroom"
    ):
        return gr.update(visible=True)

    return gr.update(visible=False)


def generate_layout(requirements, state, selected):

    if not requirements:
        raise gr.Error(
            "Generate a bathroom recommendation first."
        )

    if requirements.get("request_type") != "full_bathroom":
        raise gr.Error(
            "Layout generation is available for Complete Bathroom designs."
        )

    if not state:
        raise gr.Error(
            "Generate a bathroom recommendation first."
        )

    # Select the currently displayed recommendation.
    index = 0

    if selected:
        try:
            index = int(selected.split()[-1]) - 1
        except (ValueError, IndexError):
            index = 0

    if index < 0 or index >= len(state):
        index = 0

    recommendations = state[index].get("recommendations")

    if recommendations is None or recommendations.empty:
        raise gr.Error(
            "No recommended products are available for the layout."
        )

    width = requirements.get("bathroom_width_ft")
    depth = requirements.get("bathroom_depth_ft")

    if width is None or depth is None:
        raise gr.Error(
            "Bathroom width and depth are required."
        )

    # Create layout from the actual selected recommendation.
    fig = create_layout(
        width,
        depth,
        recommendations
    )

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    layout_path = output_dir / "bathroom_layout.png"

    fig.savefig(
        layout_path,
        dpi=160,
        bbox_inches="tight"
    )

    plt.close(fig)

    return str(layout_path)


  
# OPEN LAYOUT IN NEW TAB
  

def layout_html(image_path):

    if not image_path:
        return ""

    path = Path(image_path)

    if not path.exists():
        return ""


    import base64

    image_data = base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")

    image_uri = f"data:image/png;base64,{image_data}"

    return f"""
    <div style="
        text-align:center;
        margin-top:14px;
        margin-bottom:10px;
    ">
        <a
            href="{image_uri}"
            target="_blank"
            rel="noopener noreferrer"
            style="
                display:inline-block;
                padding:12px 24px;
                border-radius:8px;
                background:#f97316;
                color:white;
                text-decoration:none;
                font-weight:600;
                font-size:14px;
            "
        >
            Open Layout in New Tab ↗
        </a>
    </div>
    """


  
# CSS
  

CSS = r"""
:root {
    --page: #0b0b0b;
    --surface: #131313;
    --surface-2: #171717;
    --border: #292929;
    --border-soft: #222;
    --text: #f2f2f2;
    --muted: #9a9a9a;
    --muted-2: #777;
    --accent: #f97316;
}

.gradio-container {
    max-width: 1180px !important;
    margin: auto !important;
    padding: 34px 38px 64px !important;
    background: var(--page) !important;
}

body {
    background: var(--page) !important;
}

/* ---------- Hero ---------- */

h1 {
    font-size: 38px !important;
    line-height: 1.08 !important;
    font-weight: 750 !important;
    letter-spacing: -1.1px !important;
    margin: 4px 0 8px !important;
}

.brand-subtitle {
    color: #a8a8a8;
    font-size: 15px;
    line-height: 1.65;
    max-width: 720px;
    margin-bottom: 25px;
}

/* ---------- How It Works ---------- */

.workflow-heading {
    color: #777;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: 1.55px;
    margin: 4px 0 10px;
}

.workflow {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 0 0 20px;
}

.workflow-step {
    position: relative;
    min-height: 86px;
    padding: 14px 15px 13px;
    border: 1px solid #292929;
    border-radius: 11px;
    background: #111111;
    overflow: hidden;
}

.workflow-step::after {
    content: "";
    position: absolute;
    left: 15px;
    right: 15px;
    bottom: 0;
    height: 2px;
    background: #2a2a2a;
}

.workflow-step:first-child::after {
    background: #f97316;
}

.workflow-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #1d1d1d;
    border: 1px solid #383838;
    color: #d8d8d8;
    font-size: 10px;
    font-weight: 750;
    margin-bottom: 10px;
}

.workflow-title {
    color: #ededed;
    font-size: 13px;
    font-weight: 680;
    letter-spacing: 0;
}

.workflow-sub {
    color: #777;
    font-size: 10px;
    line-height: 1.45;
    margin-top: 4px;
}

.workflow-line {
    display: none;
}

/* ---------- Example ---------- */

.example-card {
    border: 1px solid #292929;
    border-radius: 11px;
    background: #121212;
    padding: 13px 16px;
    margin: 0 0 24px;
}

.example-title,
.section-label {
    color: #777;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: 1.55px;
}

.example-title {
    margin-bottom: 5px;
}

.example-text {
    color: #dcdcdc;
    font-size: 13px;
    line-height: 1.5;
}

/* ---------- Mode ---------- */

.mode-box {
    border: 1px solid var(--border);
    border-radius: 13px;
    background: var(--surface);
    padding: 16px 18px;
    margin-bottom: 11px;
}

.mode-title {
    font-size: 16px;
    font-weight: 680;
    margin-bottom: 4px;
}

.mode-description {
    color: #8f8f8f;
    font-size: 13px;
    line-height: 1.5;
}

textarea {
    font-size: 15px !important;
    line-height: 1.55 !important;
}

/* ---------- Forms ---------- */

.custom-panel {
    border: 1px solid var(--border);
    border-radius: 13px;
    background: var(--surface);
    padding: 20px;
}

.custom-heading {
    font-size: 17px;
    font-weight: 680;
    margin-bottom: 14px;
}

.primary-btn {
    min-height: 48px !important;
    border-radius: 9px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05px !important;
}

button.primary {
    box-shadow: none !important;
}

.gradio-dropdown,
.gradio-number,
.gradio-textbox,
.gradio-checkbox,
.gradio-radio {
    border-radius: 9px !important;
}

/* ---------- Results ---------- */

.results-heading {
    margin-top: 31px;
    margin-bottom: 5px;
}

.results-title {
    font-size: 25px !important;
    line-height: 1.2 !important;
    margin: 4px 0 4px !important;
    font-weight: 700 !important;
}

.results-subtitle,
.product-subtitle,
.layout-subtitle {
    color: #858585;
    font-size: 13px;
    line-height: 1.55;
}

.profile-card {
    border: 1px solid var(--border);
    border-radius: 13px;
    background: var(--surface);
    padding: 18px;
    margin-top: 7px;
}

.profile-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 17px 20px;
}

.profile-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.profile-label {
    color: #747474;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 1.25px;
}

.profile-value {
    color: #ededed;
    font-size: 14px;
    line-height: 1.4;
}

.product-heading {
    margin-top: 24px;
    margin-bottom: 10px;
}

.product-title {
    color: #eeeeee;
    font-size: 20px;
    font-weight: 700;
    margin: 4px 0 3px;
}

.total-card {
    border: 1px solid #343434;
    border-radius: 13px;
    background: linear-gradient(180deg, #171717, #131313);
    padding: 17px 20px;
    margin-top: 12px;
}

.total-label {
    display: block;
    color: #777;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 1.45px;
}

.total-value {
    display: block;
    color: #f3f3f3;
    font-size: 29px;
    line-height: 1.15;
    font-weight: 750;
    margin: 5px 0 4px;
}

.total-sub {
    display: block;
    color: #909090;
    font-size: 12px;
}

/* ---------- Selector ---------- */

.alternative-box {
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
    padding: 14px 16px;
    margin-top: 14px;
}

/* ---------- Layout ---------- */

.layout-intro {
    margin-top: 30px;
    margin-bottom: 10px;
}

.layout-title {
    color: #eeeeee;
    font-size: 20px;
    font-weight: 700;
    margin: 4px 0 3px;
}

.layout-output {
    border: 1px solid var(--border);
    border-radius: 13px;
    overflow: hidden;
}

.gradio-image {
    border-radius: 13px !important;
}

@media (max-width: 800px) {
    .gradio-container {
        padding: 24px 18px 45px !important;
    }

    .workflow {
        grid-template-columns: 1fr;
    }

    .workflow-step {
        min-height: auto;
    }

    .profile-grid {
        grid-template-columns: 1fr 1fr;
    }
}

footer{
display: none !important;
}

@media (max-width: 520px) {
    h1 {
        font-size: 31px !important;
    }

    .workflow-title {
        font-size: 12px;
    }

    .workflow-sub {
        font-size: 10px;
    }

    .profile-grid {
        grid-template-columns: 1fr;
    }
}
"""



  
# UI
  

with gr.Blocks(
    title="Bathroom Recommender and Design System"
) as demo:

    gr.Markdown(
        """
#  AI Bathroom Designer

<div class="brand-subtitle">
Tell us what you want, or choose your preferences yourself.
We’ll use your choices to create a personalized bathroom recommendation.
</div>
"""
    )

    gr.Markdown(
        """
<div class="workflow-heading">HOW IT WORKS</div>
<div class="workflow">
    <div class="workflow-step">
        <div class="workflow-number">1</div>
        <div class="workflow-title">Tell us what you want</div>
        <div class="workflow-sub">Describe your needs, budget, style and bathroom size.</div>
    </div><div class="workflow-step">
        <div class="workflow-number">2</div>
        <div class="workflow-title">Review your options</div>
        <div class="workflow-sub">Compare complete bathroom combinations that fit your requirements.</div>
    </div><div class="workflow-step">
        <div class="workflow-number">3</div>
        <div class="workflow-title">Create your layout</div>
        <div class="workflow-sub">Visualize the selected bathroom arrangement in 2D.</div>
    </div>
</div>
<div class="example-card">
<div class="example-title">TRY AN EXAMPLE</div>
<div class="example-text">
“I want a modern bathroom under Rs 
1.5 lakh. My bathroom is 8 feet wide and 10 feet deep. I want to save water.”
</div>
</div>
"""
    )

    gr.Markdown(
        """
<div class="mode-box">
<div class="mode-title">How would you like to start?</div>
<div class="mode-description">
Describe your bathroom naturally, or use the guided options for more control.
</div>
</div>
"""
    )

    design_mode = gr.Radio(
        choices=[
            "Tell us what you need",
            "Choose your preferences"
        ],
        value="Tell us what you need",
        label="How would you like to design?"
    )

      
    #Top-K control
      

    with gr.Row():

        top_k = gr.Dropdown(
            choices=[
                1,
                2,
                3,
                4,
                5
            ],
            value=3,
            label="Number of options",
            info=(
                "Complete bathrooms: alternative combinations. "
                "Specific products: top products per category."
            ),
            scale=1
        )

      
     #Natural language panel
      

    with gr.Column(
        visible=True
    ) as natural_panel:

        gr.Markdown(
            '<div class="section-label">TELL US WHAT YOU NEED</div>'
        )

        user_input = gr.Textbox(
            label="",
            placeholder=(
                "Tell us about your bathroom, budget, style, size, "
                "water-saving needs, or the products you want."
            ),
            lines=5
        )

        natural_generate = gr.Button(
            "Generate Recommendation",
            variant="primary",
            elem_classes=["primary-btn"]
        )

      
     #Customize panel
      

    with gr.Column(
        visible=False,
        elem_classes=["custom-panel"]
    ) as custom_panel:

        gr.Markdown(
            '<div class="custom-heading">Choose Your Bathroom Preferences</div>'
        )

        design_type = gr.Radio(
            choices=[
                "Complete Bathroom",
                "Specific Products"
            ],
            value="Complete Bathroom",
            label="What would you like to design?"
        )

        with gr.Row():

            budget = gr.Number(
                label="Your Maximum Budget (₹)",
                value=150000,
                minimum=1,
                precision=0
            )

            style = gr.Dropdown(
                choices=[
                    "No preference",
                    "Modern",
                    "Minimalist",
                    "Luxury",
                    "Traditional",
                    "Japanese Zen"
                ],
                value="No preference",
                label="Style"
            )

            priority = gr.Dropdown(
                choices=[
                    "Best Overall",
                    "Water Saving",
                    "Luxury"
                ],
                value="Best Overall",
                label="What matters most?"
            )

        with gr.Row(
            visible=True
        ) as dimensions_row:

            width = gr.Number(
                label="Bathroom Width (ft)",
                value=8,
                minimum=0.1
            )

            depth = gr.Number(
                label="Bathroom Depth (ft)",
                value=10,
                minimum=0.1
            )

        with gr.Column(
            visible=False
        ) as product_selection_panel:

            gr.Markdown(
                '<div class="section-label">WHAT WOULD YOU LIKE TO INCLUDE?</div>'
            )

            with gr.Row():

                toilet = gr.Checkbox(
                    label="Toilet",
                    value=True
                )

                faucet = gr.Checkbox(
                    label="Faucet",
                    value=True
                )

                shower = gr.Checkbox(
                    label="Shower",
                    value=True
                )

                vanity = gr.Checkbox(
                    label="Vanity",
                    value=True
                )

        custom_generate = gr.Button(
            "Generate Recommendation",
            variant="primary",
            elem_classes=["primary-btn"]
        )

      
     #Outputs
      

    gr.Markdown(
        """
<div class="results-heading">
    <div class="section-label">YOUR DESIGN</div>
    <h2 class="results-title">Your Recommendation</h2>
    <div class="results-subtitle">
        Review the design details and the products selected for your requirements.
    </div>
</div>
"""
    )

    status = gr.Markdown("")

    gr.Markdown(
        "### Your Design Summary"
    )

    extracted_requirements = gr.Markdown(
        "Your design details will appear here."
    )

    # Hidden state containing all generated bathroom bundles.
    recommendation_state = gr.State([])
    layout_requirements_state = gr.State({})

    # User can switch between generated bundles.
    recommendation_selector = gr.Dropdown(
        choices=[],
        label="Compare another option",
        info="Switch between the alternative bathroom combinations.",
        visible=False
    )

    gr.Markdown(
        """
<div class="product-heading">
    <div class="section-label">SELECTED PRODUCTS</div>
    <div class="product-title">Your Recommended Products</div>
    <div class="product-subtitle">
        A complete set selected to match your space, budget and preferences.
    </div>
</div>
"""
    )

    recommendations_table = gr.Dataframe(
        value=empty_table(),
        headers=[
            "Category",
            "Product Name",
            "Price"
        ],
        datatype=[
            "str",
            "str",
            "str"
        ],
        interactive=False,
        wrap=True,
        column_widths=[
            "16%",
            "64%",
            "20%"
        ]
    )

    total_cost = gr.HTML("")

      
    # 2D Bathroom Layout
      

    gr.Markdown(
        """
<div class="layout-intro">
    <div class="section-label">SPACE PLANNER</div>
    <div class="layout-title">Visualize Your Bathroom</div>
    <div class="layout-subtitle">
        See how your selected products can be arranged within the bathroom dimensions you provided.
    </div>
</div>
"""
    )

    generate_layout_btn = gr.Button(
        "Create My Bathroom Layout",
        variant="primary",
        visible=False,
        elem_classes=["primary-btn"]
    )

    layout_output = gr.Image(
        label="Your 2D Bathroom Layout",
        type="filepath",
        visible=False,
        interactive=False,
        buttons=[]
    )

    layout_new_tab = gr.HTML("")


      
    # Mode switching
      

    def switch_mode(mode):

        if mode == "Tell us what you need":

            return (
                gr.update(visible=True),
                gr.update(visible=False)
            )

        return (
            gr.update(visible=False),
            gr.update(visible=True)
        )

    def switch_design_type(design_type_value):

        if design_type_value == "Complete Bathroom":
            return (
                gr.update(visible=True),
                gr.update(visible=False)
            )

        return (
            gr.update(visible=False),
            gr.update(visible=True)
        )

    design_mode.change(
        fn=switch_mode,
        inputs=design_mode,
        outputs=[
            natural_panel,
            custom_panel
        ]
    )

      
    design_type.change(
        fn=switch_design_type,
        inputs=[design_type],
        outputs=[
            dimensions_row,
            product_selection_panel
        ]
    )

    # Natural language connection
      

    natural_generate.click(
        fn=generate_from_text,
        inputs=[
            user_input,
            top_k
        ],
        outputs=[
            status,
            extracted_requirements,
            recommendations_table,
            total_cost,
            recommendation_selector,
            recommendation_state,
            layout_requirements_state
        ]
    ).then(
        fn=update_layout_button,
        inputs=[layout_requirements_state],
        outputs=[generate_layout_btn]
    )

      
    # Custom form connection
      

    custom_generate.click(
        fn=generate_from_form,
        inputs=[
            design_type,
            budget,
            width,
            depth,
            style,
            priority,
            toilet,
            faucet,
            shower,
            vanity,
            top_k
        ],
        outputs=[
            status,
            extracted_requirements,
            recommendations_table,
            total_cost,
            recommendation_selector,
            recommendation_state,
            layout_requirements_state
        ]
    ).then(
        fn=update_layout_button,
        inputs=[layout_requirements_state],
        outputs=[generate_layout_btn]
    )

      
    # Alternative recommendation selector
      

    recommendation_selector.change(
        fn=show_selected_recommendation,
        inputs=[
            recommendation_selector,
            recommendation_state
        ],
        outputs=[
            recommendations_table,
            total_cost
        ]
    )

      
    # Generate Layout
      

    generate_layout_btn.click(
        fn=generate_layout,
        inputs=[
            layout_requirements_state,
            recommendation_state,
            recommendation_selector
        ],
        outputs=[
            layout_output
        ]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[
            layout_output
        ]
    ).then(
        fn=layout_html,
        inputs=[
            layout_output
        ],
        outputs=[
            layout_new_tab
        ]
    )



  
# LAUNCH
  

if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Base(
            primary_hue="orange",
            neutral_hue="slate"
        ),
        css=CSS,
        allowed_paths=["outputs"],
    )
