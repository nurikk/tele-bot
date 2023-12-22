def generate_prompt(data: dict[str, str]) -> str:
    prompt = f"Generate a postcard for my {data['relationship']} for {data['reason']}. He is {data['description']}. Depict {data['depiction']}. Use {data['style']} style. Add appropriate text with congratulations with {data['reason']}."
    return prompt
