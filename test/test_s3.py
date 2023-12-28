import os

import pytest

from src import s3


@pytest.mark.asyncio
async def test_upload():
    await s3.upload_image(b'123')