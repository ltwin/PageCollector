"""
入口，调用爬虫
"""
import asyncio
import os
import sys
import traceback

from loguru import logger

import common as cm
from exceptions import DupSpidersError
from _spider import DEFAULT_SPIDER_NAME

sys.path.append('spiders')
sys.path.append('pipelines')


def load_spiders():
    spiders = []
    spider_names = []
    for item in os.listdir('spiders'):
        if os.path.isfile(os.path.join('spiders', item)):
            package = __import__(os.path.splitext(item)[0])
            for attr in dir(package):
                obj = getattr(package, attr)
                try:
                    obj_name = obj.__base__.__name__
                except AttributeError:
                    continue
                if obj_name == '_Spider':
                    spiders.append(obj)
                    spider_names.append(obj.__spider__)
    if len(set(spider_names)) != len(spider_names):
        raise DupSpidersError
    logger.info('Load spiders: %s' % spiders)
    return spiders


def load_pipelines():
    pipelines = []
    for item in os.listdir('pipelines'):
        if os.path.isfile(os.path.join('pipelines', item)):
            package = __import__(os.path.splitext(item)[0])
            for attr in dir(package):
                obj = getattr(package, attr)
                try:
                    obj_name = obj.__base__.__name__
                except AttributeError:
                    continue
                if obj_name == '_Pipeline':
                    pipelines.append(obj)
    logger.info('Load pipelines: %s' % pipelines)
    return pipelines


def crawl_one_site(url, base_output_dir, max_depth,
                   concurrent_limit, spider=None, level=0,
                   splash=False, proxy=False,
                   bs64encode_filename=False,
                   user_agent=None, timeout=5 * 60,
                   time_wait=None):
    """递归下载一个站点"""
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    semaphore = asyncio.Semaphore(value=concurrent_limit)
    domain = cm.get_host_from_url(url)
    output_dir = os.path.join(base_output_dir, domain)
    if not os.path.isdir(output_dir):
        os.system('mkdir -p %s' % output_dir)
    if not spider:
        spider = DEFAULT_SPIDER_NAME
    spiders = load_spiders()
    spider_obj = None
    for SClass in spiders:
        if SClass.__spider__ == spider:
            spider_obj = SClass(
                site=url,
                output_dir=output_dir,
                max_depth=max_depth,
                semaphore=semaphore,
                level=level,
                splash=splash,
                proxy=proxy,
                bs64encode_filename=bs64encode_filename,
                user_agent=user_agent,
                timeout=timeout,
                time_wait=time_wait
            )
            break
    if not spider_obj:
        logger.warning('No spider matched for url: {}, '
                       'whose s_name is: {}'.format(url, spider))
        return
    pipelines = load_pipelines()
    for PClass in pipelines:
        if PClass.__spider__ == spider or PClass.__spider__ is None:
            pipeline = PClass()
            for method in dir(pipeline):
                if method.startswith('pipe_'):
                    # 拥有可执行管道方法则添加管道
                    spider_obj.add_pipeline(pipeline)
                    break
    try:
        spider_obj.run()
    except:
        logger.error('Error occurred while running: '
                     '{}'.format(traceback.format_exc()))
