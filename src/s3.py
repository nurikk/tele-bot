from hashlib import md5
from io import BytesIO

import aioboto3


class S3Uploader:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, aws_region: str, s3_bucket_name: str):
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        self.s3_bucket_name = s3_bucket_name

    async def upload_image(self, image: bytes) -> str:
        file_path = f'images/{md5(image).hexdigest()}.png'
        async with self.session.client("s3") as s3:
            await s3.upload_fileobj(BytesIO(image), self.s3_bucket_name, file_path)

        return file_path
