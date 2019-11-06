"""
Author: lt
Date: 2019-11-05
Desc: 爬虫调度任务
"""
import dramatiq

from dramatiq.results import Results
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results.backends import RedisBackend
from dramatiq.rate_limits import ConcurrentRateLimiter

import config as conf

from entrance import crawl_one_site
from tasks import settings as st


DISTRIBUTED_MUTEX = None
if st.CONCURRENT_LIMIT:
    # 建立并发控制器
    backend = RedisBackend(
        host=conf.REDIS_HOST,
        port=conf.REDIS_PORT,
        db=conf.BROKER_DB,
        password=conf.REDIS_PWD
    )
    DISTRIBUTED_MUTEX = ConcurrentRateLimiter(
        backend=backend, key='distributed-mutex', limit=st.CONCURRENT_LIMIT)
redis_broker = RedisBroker(
    host=conf.REDIS_HOST,
    port=conf.REDIS_PORT,
    db=conf.BROKER_DB,
    password=conf.REDIS_PWD
)
STORE_RESULTS = False
if conf.RESULT_BACKEND_DB:
    redis_broker.add_middleware(
        Results(
            backend=RedisBackend(
                host=conf.REDIS_HOST,
                port=conf.REDIS_PORT,
                db=conf.RESULT_BACKEND_DB,
                password=conf.REDIS_PWD
            )
        )
    )
    STORE_RESULTS = True
dramatiq.set_broker(redis_broker)


def _crawler(task):
    """
    分布式调度的爬虫执行函数
    :param task: 爬取任务
        可以是str类型，如：http://www.example.com
        可以是dict类型，遵循以下格式（其中url为必选）：
            {
                "url": "http://www.example.com",
                "base_output_dir": "dir/to/save",
                "concurrent_limit": <int>,
                "max_depth": <int>,
                "level": 0/1/2,
                "user_agent": "",
                "use_splash": True/False,
                "use_proxy": True/False,
                "bs64": True/False
            }
    :return:
    """
    if isinstance(task, str):
        url = task
        base_output_dir = conf.DEFAULT_OUTPUT_DIR
        concurrent_limit = conf.CONCURRENT_LIMIT
        max_depth = conf.MAX_DEPTH
        level = conf.LEVEL
        user_agent = conf.SPECIFIED_USER_AGENT
        use_splash = conf.USE_SPLASH
        use_proxy = conf.USE_IP_PROXY
        bs64 = conf.BS64_FILENAME
    elif isinstance(task, dict):
        url = task['url']
        base_output_dir = task.get('base_output_dir', conf.DEFAULT_OUTPUT_DIR)
        concurrent_limit = task.get('concurrent_limit', conf.CONCURRENT_LIMIT)
        max_depth = task.get('max_depth', conf.MAX_DEPTH)
        level = task.get('level', conf.LEVEL)
        user_agent = task.get('user_agent', conf.SPECIFIED_USER_AGENT)
        use_splash = task.get('use_splash', conf.USE_SPLASH)
        use_proxy = task.get('use_proxy', conf.USE_IP_PROXY)
        bs64 = task.get('bs64', conf.BS64_FILENAME)
    else:
        raise TypeError('Invalid task input!')

    if DISTRIBUTED_MUTEX:
        with DISTRIBUTED_MUTEX:
            crawl_one_site(
                url=url,
                base_output_dir=base_output_dir,
                max_depth=max_depth,
                concurrent_limit=concurrent_limit,
                level=level,
                splash=use_splash,
                proxy=use_proxy,
                bs64encode_filename=bs64,
                user_agent=user_agent
            )
    else:
        crawl_one_site(
            url=url,
            base_output_dir=base_output_dir,
            max_depth=max_depth,
            concurrent_limit=concurrent_limit,
            level=level,
            splash=use_splash,
            proxy=use_proxy,
            bs64encode_filename=bs64,
            user_agent=user_agent
        )


@dramatiq.actor(
    max_age=st.MAX_AGE,
    max_retries=st.MAX_RETRIES, min_backoff=st.MIN_BACKOFF,
    time_limit=st.TIME_LIMIT)
def on_failure():
    pass


@dramatiq.actor(
    max_age=st.MAX_AGE,
    max_retries=st.MAX_RETRIES, min_backoff=st.MIN_BACKOFF,
    time_limit=st.TIME_LIMIT)
def ont_success():
    pass


if STORE_RESULTS:
    crawler = dramatiq.actor(
        store_results=True, max_age=st.MAX_AGE,
        max_retries=st.MAX_RETRIES, min_backoff=st.MIN_BACKOFF,
        time_limit=st.TIME_LIMIT
    )(_crawler)
else:
    crawler = dramatiq.actor(
        max_age=st.MAX_AGE,
        max_retries=st.MAX_RETRIES,
        min_backoff=st.MIN_BACKOFF,
        time_limit=st.TIME_LIMIT
    )(_crawler)
