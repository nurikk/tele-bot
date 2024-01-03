import os

import pytest

from src import s3


@pytest.mark.asyncio
async def test_upload(settings):
    s3_uploader = s3.S3Uploader(aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key,
                                aws_region=settings.aws_region, s3_bucket_name=settings.s3_bucket_name)

    await s3_uploader.upload_image(b'123')
