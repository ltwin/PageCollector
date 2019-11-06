"""
测试入口脚本
"""
from tasks.spider_task import crawler


crawler.send('https://dramatiq.io/guide.html')
