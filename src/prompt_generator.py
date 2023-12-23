import i18n


def generate_prompt(data: dict[str, str], locale: str) -> str:
    return i18n.t("prompt", locale=locale, **data)
