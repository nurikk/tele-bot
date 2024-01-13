from datetime import datetime
from unittest.mock import patch

from src.main import init_i18n
from src.prompt_generator import generate_prompt


def test_generate_prompt():
    init_i18n()

    assert generate_prompt(data={"reason": "reason",
                                 "relationship": "relationship",
                                 "description": "description",
                                 "depiction": "depiction"}, locale="en") != ''

    assert generate_prompt(data={"reason": "reason",
                                 "relationship": "relationship",
                                 "description": "description",
                                 "depiction": "depiction"}, locale="ru") != ''
