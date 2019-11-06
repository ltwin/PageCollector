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

from spider import crawl_one_site
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


def _crawler(url):
    base_output_dir = conf.DEFAULT_OUTPUT_DIR
    concurrent_limit = conf.CONCURRENT_LIMIT
    max_depth = conf.MAX_DEPTH
    level = conf.LEVEL
    user_agent = conf.SPECIFIED_USER_AGENT
    use_splash = conf.USE_SPLASH
    use_proxy = conf.USE_IP_PROXY
    bs64 = conf.BS64_FILENAME

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
