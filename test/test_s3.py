import os

import pytest

from src import s3


@pytest.mark.asyncio
async def test_upload(settings):
    s3_uploader = s3.S3Uploader(aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key,
                                aws_region=settings.aws_region, s3_bucket_name=settings.s3_bucket_name)

    path = await s3_uploader.upload_image_from_url('https://upload.wikimedia.org/wikipedia/commons/4/4d/Cat_November_2010-1a.jpg')


