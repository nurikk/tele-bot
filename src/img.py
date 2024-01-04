import abc

from imgproxy import ImgProxy


class Proxy(abc.ABC):
    def get_thumbnail(self, url: str, width=500, height=500) -> str:
        raise NotImplementedError()

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
    def __init__(self,
                 imgproxy_hostname: str,
                 imgproxy_port: str,
                 imgproxy_key: str = None,
                 imgproxy_salt: str = None
                 ):
        self.imgproxy_hostname = imgproxy_hostname
        self.imgproxy_port = imgproxy_port
        self.imgproxy_key = imgproxy_key
        self.imgproxy_salt = imgproxy_salt

    def get_thumbnail(self, url: str, width=500, height=500) -> str:
        return ImgProxy(url,
                        proxy_host=f'http://{self.imgproxy_hostname}:{self.imgproxy_port}',
                        key=self.imgproxy_key,
                        salt=self.imgproxy_salt,
                        width=width, height=height, extension='png')()

    def get_full_image(self, url: str) -> str:
        return ImgProxy(url,
                        proxy_host=f'http://{self.imgproxy_hostname}:{self.imgproxy_port}',
                        key=self.imgproxy_key,
                        salt=self.imgproxy_salt)()
