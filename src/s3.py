from hashlib import md5
from io import BytesIO

import aioboto3

from src.settings import settings


async def upload_image(image: bytes) -> str:
    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region
    )
    file_path = f'images/{md5(image).hexdigest()}.png'
    async with session.client("s3") as s3:
        await s3.upload_fileobj(BytesIO(image), settings.s3_bucket_name, file_path)

    return file_path
