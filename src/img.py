from imgproxy import ImgProxy


class ImageProxy:
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
