from imgproxy import ImgProxy

from src.settings import settings


def get_thumbnail(url: str) -> str:
    img_url = ImgProxy(url,
                       proxy_host=f'http://{settings.imgproxy_hostname}:{settings.imgproxy_port}',
                       width=800, height=400)
    return img_url()
