from src.img import ImageProxy


def test_thumbnail(settings):
    image_url = f's3://{settings.s3_bucket_name}/images/2b7e6167f805dbc4a733da84da99eb05.png'

    proxy = ImageProxy(imgproxy_hostname=settings.imgproxy_hostname,
                       imgproxy_key=settings.imgproxy_key,
                       imgproxy_salt=settings.imgproxy_salt)
    assert proxy.get_thumbnail(image_url) == ''
