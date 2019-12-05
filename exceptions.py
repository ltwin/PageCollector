"""
爬虫定义异常
"""


class SpiderError(Exception):
    """爬虫异常"""
    def __init__(self, message='Error occurred while crawling!'):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value


class DupSpidersError(Exception):
    def __init__(self, message='You cannot define two crawlers with the same name'):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value
