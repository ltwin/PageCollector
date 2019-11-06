"""
测试入口脚本
"""
from tasks.spider_task import crawler


crawler.send('https://dramatiq.io/guide.html')
crawler.send(
    {
        "url": "http://www.wuhan.gov.cn/",
        "concurrent_limit": 128,
        "max_depth": 2,
        "level": 2,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/77.0.3865.120 Safari/537.36",
        "use_splash": False,
        "use_proxy": False,
        "bs64": False
    }
)
