"""
dramatiq设置
"""
# 消息的最大生命周期（在生命周期内，相同的函数和参数会直接返回旧数据，而不会运行任务），单位ms
MAX_AGE = 1000
# 出错最大重试次数
MAX_RETRIES = 3
# 重试的最小间隔时间，单位ms
MIN_BACKOFF = 5000
# 限制任务的并发数，为空则不限制
CONCURRENT_LIMIT = None
# 限制执行超时时间，不传则不限制，默认600000，单位ms
TIME_LIMIT = 600000
