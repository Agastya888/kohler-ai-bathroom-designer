import os
import json

from dotenv import load_dotenv
from openai import OpenAI


    
# LOAD API KEY
    

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found.\n"
        "Please add your Gemini API key to the .env file."
    )


    
# GEMINI CLIENT
    

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

MODEL = "gemini-3.1-flash-lite"


    
# ALLOWED VALUES
    

ALLOWED_STYLES = {
    "Modern",
    "Minimalist",
    "Luxury",
    "Traditional",
    "Japanese Zen"
}

ALLOWED_PRIORITIES = {
    "Best Overall",
    "Water Saving",
    "Luxury"
}

ALLOWED_CATEGORIES = {
    "Toilet",
    "Faucet",
    "Shower",
    "Vanity"
}

ALLOWED_REQUEST_TYPES = {
    "full_bathroom",
    "product_search"
}


    
# VALIDATE REQUIREMENTS
    

def validate_requirements(requirements):

    required_fields = [
        "request_type",
        "requested_categories",
        "budget",
        "desired_style",
        "priority",
        "bathroom_width_ft",
        "bathroom_depth_ft",
        "missing_information"
    ]

    for field in required_fields:
        if field not in requirements:
            raise ValueError(
                f"Missing field in Gemini response: {field}"
            )

    if requirements["request_type"] not in ALLOWED_REQUEST_TYPES:
        raise ValueError(
            f"Invalid request_type: {requirements['request_type']}"
        )

    categories = requirements["requested_categories"]

    if not isinstance(categories, list) or not categories:
        raise ValueError(
            "requested_categories must be a non-empty list."
        )

    for category in categories:
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}"
            )

    budget = requirements["budget"]

    if budget is not None:
        if not isinstance(budget, (int, float)):
            raise ValueError(
                "Budget must be a number or null."
            )

        if budget <= 0:
            raise ValueError(
                "Budget must be greater than zero."
            )

    style = requirements["desired_style"]

    if style is not None and style not in ALLOWED_STYLES:
        raise ValueError(
            f"Invalid style: {style}"
        )

    priority = requirements["priority"]

    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(
            f"Invalid priority: {priority}"
        )

    width = requirements["bathroom_width_ft"]

    if width is not None:
        if not isinstance(width, (int, float)):
            raise ValueError(
                "Bathroom width must be a number or null."
            )

        if width <= 0:
            raise ValueError(
                "Bathroom width must be greater than zero."
            )

    depth = requirements["bathroom_depth_ft"]

    if depth is not None:
        if not isinstance(depth, (int, float)):
            raise ValueError(
                "Bathroom depth must be a number or null."
            )

        if depth <= 0:
            raise ValueError(
                "Bathroom depth must be greater than zero."
            )

    missing_information = requirements["missing_information"]

    if not isinstance(missing_information, list):
        raise ValueError(
            "missing_information must be a list."
        )

    allowed_missing = {
        "budget",
        "bathroom dimensions"
    }

    for item in missing_information:
        if item not in allowed_missing:
            raise ValueError(
                f"Invalid missing_information value: {item}"
            )

    # Full bathroom needs dimensions.
    if requirements["request_type"] == "full_bathroom":
        if (
            width is None
            or depth is None
        ):
            if "bathroom dimensions" not in missing_information:
                raise ValueError(
                    "Full bathroom requests require bathroom dimensions."
                )

    # Product searches do not need dimensions.
    return True


    
# EXTRACT REQUIREMENTS
    

def extract_requirements(user_input):

    if not user_input or not user_input.strip():
        raise ValueError(
            "User requirement cannot be empty."
        )

    # Normalize whitespace while preserving the user's wording.
    user_input = " ".join(user_input.strip().split())

    prompt = f"""
You are a requirement extraction system for a bathroom
product recommendation application.

The user's input is CASE-INSENSITIVE.
Treat uppercase, lowercase, and mixed-case words as equivalent.

Extract the user's requirements and return ONLY valid JSON.


# FIELDS


request_type:
- "full_bathroom" if the user wants to design/plan a complete
  bathroom.
- "product_search" if the user asks for one or more specific
  product categories.

requested_categories:
Allowed values:
- Toilet
- Faucet
- Shower
- Vanity

Category matching is CASE-INSENSITIVE.

Examples:
- toilet -> "Toilet"
- TOILET -> "Toilet"
- Toilet -> "Toilet"
- faucet -> "Faucet"
- FAUCET -> "Faucet"
- shower -> "Shower"
- vanity -> "Vanity"

For a full bathroom, always return:
["Toilet", "Faucet", "Shower", "Vanity"]

For a product search, return ONLY the categories requested.
Respect words such as "only".


budget:
- Maximum budget in INR.
- Budget expressions are CASE-INSENSITIVE.
- Convert lakh notation.
- 1 lakh = 100000
- 1.5 lakh = 150000
- 2 lakh = 200000
- "40k" or "40K" = 40000
- "rs 40k", "RS 40K", or "Rs 40K" = 40000
- For a range such as "40-50k", use the upper limit: 50000.
- If no budget is provided, use null.


desired_style:
Allowed values:
- Modern
- Minimalist
- Luxury
- Traditional
- Japanese Zen

Map natural language to the closest allowed style.
Style matching is CASE-INSENSITIVE.
If no style is specified, use null.


priority:
Allowed values:
- Best Overall
- Water Saving
- Luxury

Examples:
- save water / eco friendly / low water usage -> Water Saving
- premium / high-end -> Luxury
- otherwise -> Best Overall


bathroom_width_ft:
Bathroom width in feet. Convert other units to feet.
If not provided, use null.


bathroom_depth_ft:
Bathroom depth in feet. Convert other units to feet.
If not provided, use null.


missing_information:
Possible values:
- "budget"
- "bathroom dimensions"

Rules:
- Budget is required for both request types.
- Bathroom dimensions are required ONLY for full_bathroom.
- Product searches do NOT require dimensions.
- Style is OPTIONAL and must never be put in
  missing_information.
- If all required information is present, return [].


IMPORTANT:
- Do not invent values.
- Do not recommend products.
- Do not calculate scores.
- Return ONLY JSON.
- Do not use markdown fences.
- Treat uppercase and lowercase input as equivalent.

USER REQUIREMENT:
{user_input}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )
    except Exception as error:
        raise ValueError(
            f"Gemini API call failed: {error}"
        )

    result = response.choices[0].message.content

    if not result:
        raise ValueError(
            "Gemini returned an empty response."
        )

    result = result.strip()

    # Handle accidental ```json ... ``` responses.
    if result.startswith("```"):
        result = result.replace("```json", "", 1)
        result = result.replace("```", "")
        result = result.strip()

    try:
        requirements = json.loads(result)
    except json.JSONDecodeError:
        raise ValueError(
            "Gemini returned invalid JSON:\n"
            + result
        )

    validate_requirements(requirements)

    return requirements
    
# TEST
    

if __name__ == "__main__":

    user_input = input(
        "\nDescribe your bathroom requirements:\n> "
    )

    try:
        requirements = extract_requirements(user_input)

        print("\nExtracted Requirements:")
        print(
            json.dumps(
                requirements,
                indent=4
            )
        )

        print("\nValidation: PASSED")

    except ValueError as error:

        print("\nValidation: FAILED")
        print("Error:", error)
