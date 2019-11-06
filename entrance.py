"""
入口，调用爬虫
"""
import asyncio
import traceback

import os
from loguru import logger

import common as cm
from pipeline import Pipeline
from spider import Spider


def crawl_one_site(url, base_output_dir, max_depth,
                   concurrent_limit, level=0,
                   splash=False, proxy=False,
                   bs64encode_filename=False,
                   user_agent=None):
    """递归下载一个站点"""
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    semaphore = asyncio.Semaphore(value=concurrent_limit)
    domain = cm.get_host_from_url(url)
    output_dir = os.path.join(base_output_dir, domain)
    if not os.path.isdir(output_dir):
        os.system('mkdir -p %s' % output_dir)
    spider = Spider(
        site=url,
        output_dir=output_dir,
        max_depth=max_depth,
        semaphore=semaphore,
        level=level,
        splash=splash,
        proxy=proxy,
        bs64encode_filename=bs64encode_filename,
        user_agent=user_agent
    )
    pipeline = Pipeline()
    for method in dir(pipeline):
        if method.startswith('pipe_'):
            # 拥有可执行管道方法则添加管道
            spider.add_pipeline(pipeline)
            break
    try:
        spider.run()
    except:
        logger.error('Error occurred while running: '
                     '{}'.format(traceback.format_exc()))
