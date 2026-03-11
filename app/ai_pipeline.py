from pathlib import Path

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
    temperature: float = 0.2,
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
    temperature: float = 0.2,
) -> str:
    """Use a text model to assess whether the image description suggests risk."""
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


def extract_danger_label(text: str) -> str:
    """
    Convert model output to Y/N.

    Preference order:
    - exact trailing line Y or N
    - fallback to presence of standalone Y or N line
    - final fallback: keyword heuristic
    """
    lines = [line.strip().upper() for line in text.splitlines() if line.strip()]

    for line in reversed(lines):
        if line == "Y":
            return "Y"
        if line == "N":
            return "N"

    upper = text.upper()
    if "AT RISK" in upper or "RISK" in upper:
        return "Y"
    return "N"
