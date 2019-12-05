DEFAULT_SPIDER_NAME = 'spider'


class _Pipeline(object):
    """
    自定义数据管道基类，需自行编写处理方法，所有以pipe_开头的方法将被执行
    执行方法参数至少有一个，第一个参数将会被作为爬虫结果传输入口
    注意：当使用cli命令行调用时，管道不会生效
    数据格式为：
        {
            "task": "http://www.example.com",
            "results": {
                "http://www.example.com/a": "aaa",
                "http://www.example.com/b": "bbb"
            }
        }
    """

    __spider__ = None

    def __init__(self):
        pass
