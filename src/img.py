import abc
from typing import Optional

from imgproxy import ImgProxy


class Proxy(abc.ABC):
    @abc.abstractmethod
    def get_thumbnail(self, url: str, width=500, height=500) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_full_image(self, url: str) -> str:
        raise NotImplementedError()


class ImageOptim(Proxy):
    def __init__(self, account_id: str):
        self.account_id = account_id

    def get_thumbnail(self, url: str, width=500, height=500) -> str:
        return f"https://img.gs/{self.account_id}/{width}x{height}/{url}"

    def get_full_image(self, url: str) -> str:
        return f"https://img.gs/{self.account_id}/full/{url}"


class ImageProxy(Proxy):
    def __init__(
        self,
        imgproxy_hostname: str,
        imgproxy_key: Optional[str] = None,
        imgproxy_salt: Optional[str] = None,
    ):
        self.imgproxy_hostname = imgproxy_hostname
        self.imgproxy_key = imgproxy_key
        self.imgproxy_salt = imgproxy_salt

    def get_thumbnail(self, url: str, width=500, height=500) -> str:
        return ImgProxy(
            url,
            proxy_host=f"https://{self.imgproxy_hostname}",
            key=self.imgproxy_key,
            salt=self.imgproxy_salt,
            width=width,
            height=height,
            extension="png",
        )()

    def get_full_image(self, url: str) -> str:
        return ImgProxy(
            url,
            proxy_host=f"https://{self.imgproxy_hostname}",
            key=self.imgproxy_key,
            salt=self.imgproxy_salt,
        )()
