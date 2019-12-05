"""
自定义的爬虫类型，通过重写filter方法可以提取页面中的内容
"""
from _spider import _Spider


class Spider(_Spider):
    """
    自定义爬虫类
    """

    __spider__ = 'spider'

    def filter(self, stream):
        return stream
