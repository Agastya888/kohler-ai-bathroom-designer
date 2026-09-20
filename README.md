# KOHLER AI Bathroom Designer

An AI-assisted bathroom planning and product recommendation system that converts user requirements into personalized KOHLER bathroom product recommendations while respecting budget, space, style, and priority constraints.

The application combines **LLM-based requirement extraction**, a **constraint-aware recommendation engine**, and an **entrance-aware 2D bathroom layout generator** in an interactive Gradio interface.

---

## Overview

The **KOHLER AI Bathroom Designer** helps users plan a bathroom by understanding their requirements and selecting suitable products from a curated KOHLER product dataset.

Users can interact with the system in two ways:

1. **Natural Language Mode** — describe the bathroom requirements in everyday language.
2. **Guided Preference Mode** — manually specify budget, bathroom dimensions, style, priority, and required product categories.

For complete bathroom designs, the system generates multiple valid product combinations and allows the user to compare alternatives.

The selected recommendation can then be visualized using a **2D schematic bathroom layout** based on the actual catalog dimensions of the recommended products.

---

## Features

* Natural-language bathroom requirement input
* LLM-based requirement extraction
* Guided form-based design input
* Complete bathroom recommendations
* Specific product-category search
* Budget-aware product filtering
* Bathroom-dimension filtering
* Style-aware ranking
* Water-saving prioritization
* Luxury prioritization
* Compactness-aware ranking
* Top-K recommendation alternatives
* Product-level budget constraints
* Complete bathroom bundle optimization
* Pareto-based pruning of dominated recommendation states
* User-facing recommendation explanations
* Entrance-aware 2D bathroom layout generation
* Product footprint visualization using catalog dimensions
* Product rotation when required for layout fitting
* Fixture clearance constraints
* Protected bathroom entrance zone
* Indian currency formatting
* Submission validation suite

---

## System Architecture

The system follows a modular pipeline in which the LLM is responsible for understanding natural-language requirements, while deterministic Python components perform validation, filtering, scoring, optimization, explanation generation, and spatial layout generation.

![KOHLER AI Bathroom Designer System Architecture](<PPT,PROMPT,VIDEO/Data Flow Diagram.png>)

### Major Data Stores

```text
D1 - LLM Prompt Configuration
     System prompts and extraction instructions

D2 - Validation Configuration
     Allowed categories, styles, priorities and constraints

D3 - KOHLER Product Dataset
     Product information, prices, dimensions, styles,
     water usage and scoring attributes

D4 - Explanation Logic
     Rules used to generate factual recommendation explanations

D5 - Layout Rules
     Fixture clearance, entry protection,
     placement and orientation rules
```

---

## How It Works

### 1. User Provides Requirements

The user can either describe their requirements naturally or use the guided form.

Example:

```text
I want a modern bathroom under ₹1.5 lakh.
My bathroom is 8 feet wide and 10 feet deep.
I want to save water.
```

The guided form provides the same core requirements explicitly through fields such as:

* Budget
* Bathroom dimensions
* Style
* Priority
* Product categories

---

### 2. Requirement Extraction

For natural-language input, the LLM converts the request into structured JSON.

The extracted information includes:

* Request type
* Requested product categories
* Maximum budget
* Desired style
* Priority
* Bathroom width
* Bathroom depth
* Missing information

Example:

```json
{
    "request_type": "full_bathroom",
    "requested_categories": [
        "Toilet",
        "Faucet",
        "Shower",
        "Vanity"
    ],
    "budget": 150000,
    "desired_style": "Modern",
    "priority": "Water Saving",
    "bathroom_width_ft": 8,
    "bathroom_depth_ft": 10,
    "missing_information": []
}
```

The extracted requirements are validated before being passed to the recommendation engine.

The LLM is used for **requirement understanding and extraction**, not for directly selecting products.

---

### 3. Requirement Validation

The extracted requirements are validated against the application's supported schema.

Validation checks include:

* Request type
* Product categories
* Budget
* Style
* Priority
* Bathroom dimensions
* Missing required information

For complete bathroom recommendations, bathroom dimensions are required.

This validation layer prevents malformed or unsupported requirements from reaching the recommendation engine.

---

### 4. Hard Constraints Are Applied

The recommendation engine first applies deterministic constraints.

#### Budget Constraint

Products must satisfy:

```text
product price <= user budget
```

For complete bathroom recommendations, the combined cost of:

```text
Toilet + Faucet + Shower + Vanity
```

must remain within the user's specified budget.

#### Bathroom Dimension Constraint

Bathroom dimensions entered in feet are converted into centimeters:

```text
1 ft = 30.48 cm
```

Products are then filtered using their catalog width and depth.

The engine also considers orientation when determining whether products can fit within the available space.

#### Category Constraint

For product-specific searches, only the requested categories are considered.

For complete bathroom recommendations, the required categories are:

```text
Toilet
Faucet
Shower
Vanity
```

#### Water-Usage Constraint

For water-saving requests, products without the required water-usage information in relevant water-consuming categories are excluded.

---

## Recommendation Engine

The recommendation engine is implemented in:

```text
src/recommender.py
```

The recommendation process consists of:

```text
Requirement Validation
        ↓
Hard Constraint Filtering
        ↓
Product Scoring
        ↓
Combination Optimization
        ↓
Pareto Pruning
        ↓
Top-K Recommendation Generation
```

---

### Style Scoring

The system supports the following styles:

* Modern
* Minimalist
* Luxury
* Traditional
* Japanese Zen

Products receive a style compatibility score based on their catalog style and the user's selected preference.

Exact style matches receive the highest score, while related styles receive intermediate scores.

---

### Water Efficiency Scoring

Water efficiency is calculated independently within relevant product categories using available water-usage values.

Lower water usage results in a higher water-efficiency score.

For water-saving requests, products without usable water-consumption data in relevant categories are excluded.

---

### Compactness Scoring

Product footprint is calculated using:

```text
footprint = width × depth
```

Smaller footprints receive higher compactness scores within the relevant product category.

This allows the system to consider spatial efficiency when selecting products.

---

### Priority-Based Scoring

The weighting of product attributes changes according to the user's selected priority.

#### Water Saving

```text
Style Compatibility       40%
Water Efficiency          40%
Compactness               20%
```

#### Luxury

```text
Style Compatibility       40%
Luxury                    40%
Water Efficiency          20%
```

#### Best Overall

```text
Style Compatibility       50%
Water Efficiency          25%
Luxury                    15%
Compactness               10%
```

---

## Complete Bathroom Optimization

A complete bathroom consists of four product categories:

```text
Toilet
Faucet
Shower
Vanity
```

The optimization process evaluates valid combinations while maintaining:

* Budget compliance
* Dimension compatibility
* Category coverage
* Priority-based scoring

The optimization tracks:

```text
Total Cost
Total Score
Selected Products
```

Instead of evaluating every possible combination without pruning, the system uses Pareto-based state pruning.

---

## Pareto Pruning

A recommendation state is considered dominated when another state provides a better score at an equivalent or lower cost.

Dominated states are removed from further consideration.

Conceptually:

```text
State A:
Cost  = ₹100,000
Score = 80

State B:
Cost  = ₹100,000
Score = 85

State A is dominated by State B.
```

This reduces unnecessary states while retaining competitive cost-score combinations.

The remaining valid states are then ranked according to their recommendation score.

---

## Top-K Recommendations

The system can generate multiple complete bathroom alternatives instead of returning only one combination.

The alternatives are ranked using:

1. Total recommendation score
2. Lower total cost as the tie-breaker

This allows users to compare different valid bathroom configurations.

---

## Recommendation Explanation

The application generates factual user-facing explanations for the selected recommendations.

The explanation can communicate factors such as:

* Total project cost
* Budget utilization
* Bathroom dimensions
* Style compatibility
* Selected priority
* Product categories included
* Relevant scoring considerations

The explanation layer is implemented in:

```text
src/recommendation_explainer.py
```

The explanation generation is separate from the core recommendation logic.

---

## 2D Layout Generation

The 2D bathroom layout is implemented in:

```text
src/layout.py
```

The layout generator creates a schematic representation of the selected bathroom recommendation.

It uses the actual catalog dimensions of the selected products.

The layout considers:

* Bathroom width
* Bathroom depth
* Product width
* Product depth
* Wall margins
* Fixture clearance
* Entry clearance
* Product orientation
* Preferred fixture zones
* Protected entrance area

---

### Fixture Placement

The layout generator attempts to place the major fixtures in practical zones.

The layout includes:

```text
Shower
Vanity
Toilet
Faucet
```

The faucet is positioned on the selected vanity.

Products can be rotated when necessary to improve spatial compatibility.

The entrance area is protected to prevent fixtures from blocking the bathroom entry.

---

### Layout Output

The generated layout is a **schematic 2D visualization**, not a construction or architectural drawing.

It communicates:

* Product placement
* Product footprint
* Bathroom dimensions
* Fixture arrangement
* Entry location
* Spatial relationships

---

## Project Structure

```text
kohler-ai-bathroom-designer/
│
├── data/
│   └── KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv
│
├── notebooks/
│   └── KOHLER_AI_Bathroom_Designer_Data_Pipeline.ipynb
│
├── src/
│   ├── __init__.py
│   ├── recommender.py
│   ├── requirement_extractor.py
│   ├── recommendation_explainer.py
│   └── layout.py
│
├── outputs/
│   └── bathroom_layout.png
│
├── gradio_app.py
├── test.py
├── test_submission.py
├── requirements.txt
└── README.md
```

---

## Main Components

| File                                                        | Purpose                                                            |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| `gradio_app.py`                                             | Main Gradio application and user interface                         |
| `src/recommender.py`                                        | Product filtering, scoring, optimization and Top-K recommendations |
| `src/requirement_extractor.py`                              | LLM-based natural-language requirement extraction and validation   |
| `src/recommendation_explainer.py`                           | Generates factual explanations for recommendations                 |
| `src/layout.py`                                             | Generates the 2D bathroom layout                                   |
| `test.py`                                                   | Manual testing utility for the layout module                       |
| `test_submission.py`                                        | Submission validation suite                                        |
| `data/KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv`     | Product catalog used by the recommendation engine                  |
| `notebooks/KOHLER_AI_Bathroom_Designer_Data_Pipeline.ipynb` | Data processing and recommendation methodology notebook            |
| `outputs/`                                                  | Generated bathroom layout images                                   |

---

## Installation

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd kohler-ai-bathroom-designer
```

### 2. Install Dependencies

Install the required Python libraries:

```bash
pip install gradio pandas matplotlib python-dotenv openai
```

Alternatively, if `requirements.txt` is provided:

```bash
pip install -r requirements.txt
```

### 3. Verify the Dataset

Make sure the following file exists:

```text
data/KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv
```

The recommendation engine loads the dataset relative to the project root, so the project folder structure should be preserved.

---

## Environment Variables

Natural-language requirement extraction requires an API key for the configured LLM provider.

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

The application loads the environment variable using `python-dotenv`.

The API key should never be committed to GitHub.

Add the following to `.gitignore`:

```text
.env
```

The requirement extraction module raises an error if the required API key is unavailable.

---

## Running the Application

From the project root:

```bash
python gradio_app.py
```

On Windows:

```bash
py gradio_app.py
```

Gradio will start the local application and provide a local URL.

Open the displayed URL in a browser.

---

## Example

### Natural Language Input

```text
I want a modern bathroom under ₹1.5 lakh.
My bathroom is 8 feet wide and 10 feet deep.
I want to save water.
```

The system extracts the requirements into structured information similar to:

```json
{
    "request_type": "full_bathroom",
    "requested_categories": [
        "Toilet",
        "Faucet",
        "Shower",
        "Vanity"
    ],
    "budget": 150000,
    "desired_style": "Modern",
    "priority": "Water Saving",
    "bathroom_width_ft": 8,
    "bathroom_depth_ft": 10,
    "missing_information": []
}
```

The recommendation engine then searches the catalog for valid combinations.

The application displays:

* Design summary
* Recommended products
* Product prices
* Total project cost
* Alternative recommendations
* Recommendation explanation

For a complete bathroom design, the user can also generate a 2D layout.

---

## LLM Requirement Extraction

The natural-language requirement processing layer uses an LLM through an OpenAI-compatible API interface.

The LLM is responsible for **understanding and structuring user requirements**.

It extracts fields such as:

```text
request_type
requested_categories
budget
desired_style
priority
bathroom_width_ft
bathroom_depth_ft
missing_information
```

The extracted JSON is then validated against the application's supported:

* Request types
* Product categories
* Styles
* Priorities
* Numeric constraints

### Separation of Responsibilities

The system intentionally separates language understanding from recommendation logic.

```text
User Request → LLM → Structured Requirements → Validation Layer → Deterministic Recommendation → Product Results
```

The LLM does not directly choose products.

Product selection is performed by the deterministic recommendation engine using the curated product dataset, hard constraints, scoring functions and optimization logic.

This separation improves reproducibility and keeps recommendation decisions traceable to explicit rules.

---

## Dataset

The recommendation engine uses:

```text
KOHLER_AI_Bathroom_Designer_FINAL_DATASET_v3.csv
```

The dataset contains the catalog information required by the recommendation engine, including fields used for:

* Product identification
* Product name
* Product category
* Price
* Width
* Depth
* Style
* Water usage
* Luxury attributes
* Water-efficiency scoring
* Compactness scoring

The prototype uses a curated KOHLER product dataset for the case study.

The dataset is loaded dynamically by:

```text
src/recommender.py
```

---

## Data Pipeline Notebook

The project includes a Jupyter Notebook documenting the data and recommendation methodology:

```text
notebooks/KOHLER_AI_Bathroom_Designer_Data_Pipeline.ipynb
```

The notebook demonstrates:

* Dataset loading
* Dataset inspection
* Missing-value analysis
* Product category analysis
* Budget filtering
* Bathroom-dimension filtering
* Style scoring
* Water-efficiency scoring
* Compactness scoring
* Priority-based scoring
* Product ranking
* Pareto pruning
* Complete bathroom optimization
* Top-K recommendations
* Example product searches

The notebook is intended to provide transparency into the recommendation methodology used by the application.

---

## Tech Stack

### Programming

* Python

### User Interface

* Gradio

### Data Processing

* Pandas

### Visualization

* Matplotlib

### LLM Integration

* OpenAI-compatible API interface
* Configured LLM for requirement extraction

### Configuration

* Python Dotenv

### Recommendation

* Rule-based constraint filtering
* Weighted scoring
* Pareto pruning
* Top-K optimization

### Layout

* Matplotlib
* Catalog-based product footprints
* Constraint-aware 2D placement

---

## Testing

The repository includes a dedicated submission validation suite:

```bash
py test_submission.py
```

The validation suite tests multiple scenarios covering:

* Modern + Water Saving
* Small + Minimalist
* Luxury + Large Bathroom
* Toilet-only product search
* Japanese Zen design
* Recommendation generation
* Complete category coverage
* Budget compliance
* Catalog dimension compatibility
* 2D layout generation
* Multiple bathroom sizes
* Different user preferences

Every complete bathroom recommendation is expected to contain:

```text
Toilet
Faucet
Shower
Vanity
```

The validation suite also checks that:

* The total recommendation cost remains within the supplied budget.
* Product dimensions are compatible with the supplied bathroom dimensions.
* A valid 2D layout can be generated.

A successful validation run ends with:

```text
ALL CASES PASSED
```



### Suggested Demo Flow

1. Open the application.
2. Enter a natural-language bathroom requirement.
3. Generate recommendations.
4. Review the structured design summary.
5. Compare alternative recommendations.
6. Review selected products and total cost.
7. Review the recommendation explanation.
8. Generate the 2D bathroom layout.
9. Review the resulting spatial visualization.

### Demo Video

A project demonstration video can be linked here:

```text
https://drive.google.com/file/d/1mTjTEXPGUnrD2NjGCjzJN6JTh46dkCxO/view?usp=drive_link
```

---

## Project Objective

The goal of the project is to demonstrate how an AI-assisted system can transform natural-language bathroom requirements into practical, constraint-aware product recommendations and a visual bathroom plan.

The system combines:

```text
Natural Language Understanding
            +
Requirement Validation
            +
Deterministic Recommendation
            +
Constraint Optimization
            +
Recommendation Explanation
            +
2D Spatial Visualization
```

to create an end-to-end bathroom planning assistant.

The architecture intentionally separates the responsibilities of the LLM and the deterministic recommendation system:

```text
LLM
│
└── Understand user requirements
          │
          ▼
Structured Requirements
          │
          ▼
Deterministic Engine
│
├── Apply constraints
├── Score products
├── Optimize combinations
├── Generate alternatives
└── Validate spatial compatibility
          │
          ▼
Recommendations
          │
          ▼
2D Bathroom Visualization
```

---

## Team / Author

### KOHLER AI Bathroom Designer

Developed as part of the **KOHLER–MIT-WPU AI Research Lab Program**.

**Author**

**Agastya Gupta**
B.Tech – Computer Science & Engineering
MIT World Peace University (MIT-WPU), Pune
