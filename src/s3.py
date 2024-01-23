from hashlib import md5
from io import BytesIO

import aioboto3
import aiohttp


class S3Uploader:
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        s3_bucket_name: str,
    ):
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
        self.aws_region = aws_region
        self.s3_bucket_name = s3_bucket_name

    async def upload_image(self, image: bytes) -> str:
        file_path = f"images/{md5(image).hexdigest()}.png"
        async with self.session.client("s3") as s3:
            await s3.upload_fileobj(BytesIO(image), self.s3_bucket_name, file_path)

        return file_path

    async def upload_image_from_url(self, image_url: str) -> str:
        async with aiohttp.ClientSession() as session, session.get(image_url) as resp:
            if resp.status == 200:
                image = await resp.read()
                file_path = f"images/{md5(image).hexdigest()}.png"
                async with self.session.client("s3") as s3:
                    await s3.upload_fileobj(
                        BytesIO(image), self.s3_bucket_name, file_path
                    )
                    return file_path

    def get_full_s3_url(self, file_path: str) -> str:
        return f"s3://{self.s3_bucket_name}/{file_path}"

    def get_website_url(self, file_path: str) -> str:
        return f"http://{self.s3_bucket_name}.s3-website-{self.aws_region}.amazonaws.com/{file_path}"
