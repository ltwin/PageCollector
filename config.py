"""
配置项
"""

DAEMON = False
MAX_DEPTH = 2
# 爬取级别，0：只爬三级域名相同的链接，1：只爬二级域名相同的链接，2：所有链接均爬取
LEVEL = 0
RESULT_NUM_EACH_SITE = 10
# 进程数
PROCESS_NUM = 8
# 每个进程的协程并发数限制
CONCURRENT_LIMIT = 32
LOG_DIR = 'log'
TRY_TO_DECODE = True
CRAWL_TIMEOUT = 30

PID_DIR = 'pid'
DATA_DIR = 'data'
FAKE_UA_DATA_PATH = 'data/fake_useragent_0.1.11.json'
DEFAULT_INPUT_PATH = 'data/sites_for_collect.txt'
DEFAULT_OUTPUT_DIR = 'output'

# splash服务
USE_SPLASH = False
ENABLE_IMAGE = 0
SPLASH_TIMEOUT = 30
SPLASH_URL = 'http://localhost:8050'
SPLASH_RENDER = SPLASH_URL + '/render.html'

# IP代理池
USE_IP_PROXY = False
# IP失效之后的更换代理IP次数
PROXY_TRIED_TIMES = 10
# 请求失败之后的尝试次数
RETRY_TIMES = 3
IP_PROXY_URL = 'http://localhost:5010'
GET_ONE_PROXY_IP_URL = IP_PROXY_URL + '/get'
GET_ALL_PROXY_IPS_URL = IP_PROXY_URL + '/get_all'
DELETE_PROXY_IP_URL = IP_PROXY_URL + '/delete'
