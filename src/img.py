from imgproxy import ImgProxy


class Image:
    def __init__(self, imgproxy_hostname: str, imgproxy_port: str):
        self.imgproxy_hostname = imgproxy_hostname
        self.imgproxy_port = imgproxy_port

    def get_thumbnail(self, url: str) -> str:
        img_url = ImgProxy(url,
                           proxy_host=f'http://{self.imgproxy_hostname}:{self.imgproxy_port}',
                           width=800, height=400)
        return img_url()
