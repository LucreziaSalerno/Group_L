from pathlib import Path
import re

import ollama


def ensure_model(model_name: str) -> None:
    """Pull the model if it is not already installed locally."""
    installed = ollama.list()
    installed_names = {model.model for model in installed.models}

    if model_name not in installed_names:
        ollama.pull(model_name)


def describe_image(
    image_path: Path,
    model_name: str,
    prompt: str,
    temperature: float = 0.1,
) -> str:
    """Use a vision-capable Ollama model to describe the image."""
    ensure_model(model_name)

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [str(image_path)],
            }
        ],
        options={"temperature": temperature},
    )

    return response["message"]["content"].strip()


def assess_environmental_risk(
    description: str,
    model_name: str,
    prompt: str,
    temperature: float = 0.1,
) -> str:
    """Generate a short environmental risk explanation."""
    ensure_model(model_name)

    combined_prompt = f"{prompt}\n\nImage description:\n{description}"

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": combined_prompt,
            }
        ],
        options={"temperature": temperature},
    )

    return response["message"]["content"].strip()


def classify_environmental_risk(
    description: str,
    model_name: str,
) -> str:
    """
    Strict binary classification based directly on the image description.
    Returns only Y or N.
    """
    ensure_model(model_name)

    prompt = f"""
You are a strict binary classifier for environmental risk.

Classify the area as Y or N using ONLY the image description.

Return Y if the description clearly mentions visible signs such as:
- deforestation
- clear-cut areas
- mining pits
- tailings
- smoke
- fire scars
- flooding
- severe erosion
- strong pollution
- major land degradation
- large artificial bare-soil scars

Return N if the description mainly indicates:
- normal urban development
- intact forest
- natural mountains
- natural desert landscape
- no visible environmental damage

Important:
- Be strict but not overly cautious.
- If mining or deforestation is clearly visible, return Y.
- If there is no clear visible damage, return N.
- Return ONLY one character: Y or N

Image description:
{description}
"""

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={"temperature": 0.0},
    )

    label = response["message"]["content"].strip().upper()

    if label.startswith("Y"):
        return "Y"
    return "N"


def clean_risk_response(text: str) -> str:
    """Clean the displayed risk explanation."""
    if not text:
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()

        if re.fullmatch(r"(FINAL LABEL\s*:\s*[YN])", stripped, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"[YN]", stripped, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"[YN]\s*=\s*.*", stripped, flags=re.IGNORECASE):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
