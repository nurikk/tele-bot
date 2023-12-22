def generate_prompt(data: dict[str, str]) -> str:
    prompt = [
        f"Generate a postcard for my {data['relationship']} for {data['reason']}.",
        f"He is {data['description']}.",
        f"Depict {data['depiction']}.",
        f"Use {data['style']} style."
        f"Add appropriate text with congratulations with {data['reason']}."
    ]
    return " ".join(prompt)
