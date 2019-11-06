import asyncio
import base64
import ctypes
import fcntl
import os
import sys
import traceback

from fake_useragent import UserAgent
from loguru import logger
from multiprocessing import Queue
from pyquery import PyQuery
from urllib import parse

import common as cm
import config as conf
import constansts as cons

from ahocorasick import AcAutomaton
from pipeline import Pipeline
from proxy_utils import aio_request
from proxy_utils import request_with_proxy

queue = Queue()
os.chdir(sys.path[0])
script_path = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PROCESSES = 8


def get_domain_from_url(url, with_type=False, with_port=False):
    """
    从url中获取domain
    :param url: Perhaps like "http://www.sangfor.com.cn:80/"
    :param with_type: 是否保留协议
    :param with_port: 是否保留端口
    :return: www.sangfor.com.cn
    """
    try:
        protocol, res = parse.splittype(url)
        host, res = parse.splithost(res)
        if not host:
            host = res
        domain, port = parse.splitport(host)
        if with_type:
            domain = ''.join([protocol, ':', domain])
        if with_port:
            domain = ''.join([domain, ':', port])
        return domain
    except Exception as err:
        logger.warning('Get domain from url failed! Error: %s' % err)


def is_not_special_type_link(link):
    """
    该链接是否指向特定后缀名的资源
    :param link
    :type link: str
    """
    if link.endswith('download/app'):
        return True
    link_extension = link.split('.')[-1]
    not_in = link_extension not in cons.IGNORED_EXTENSIONS
    if not not_in:
        logger.info(
            'Ignored url: {}, its type: {}'.format(link, link_extension))
    return not_in


class Spider(object):
    """
    递归爬取批量的网站的多个子页面
    """

    def __init__(self, site, output_dir, semaphore,
                 max_depth=2, decode=True, display_path=False,
                 level=0, splash=False, proxy=False,
                 bs64encode_filename=False, user_agent=None):
        self.site = site
        self.output_dir = output_dir
        self.semaphore = semaphore
        self.max_depth = max_depth
        logger.info('The max depth to crawl for page '
                    '"{}": {}'.format(self.site, self.max_depth))
        self.decode = decode
        self.display_path = display_path
        self.level = level
        self.splash = splash
        self.proxy = proxy
        self.bs64encode_filename = bs64encode_filename
        self.user_agent = user_agent
        self.pipeline = None

        self.count = 0
        self.download_count = 0
        self.success_count = 0
        self.useless_page_count = 0
        self.result_dict = None
        self.has_crawled_pages = []
        self.init_result_cache()
        try:
            self.ac = AcAutomaton(cons.USELESS_PAGE_FEATURE)
        except Exception:
            logger.error(
                'Create AcAutomation failed! '
                'The error: %s' % traceback.format_exc()
            )
            raise

    def add_pipeline(self, obj):
        self.pipeline = obj

    def init_result_cache(self):
        self.result_dict = {
            'task': self.site,
            'results': {}
        }

    def _save(self):
        """
        保存页面到文件
        :return:
        """
        for page, content in self.result_dict['results'].items():
            if not content:
                continue
            if self.bs64encode_filename:
                # 将url用bs64加密之后作为文件名
                filename = base64.b64encode(
                    page.encode('utf-8')).decode('utf-8')
            else:
                filename = page.replace('/', '{').replace(
                    ':', '}').replace('*', '[').replace('?', '^')
            # 文件名不得长于linux长度限制
            if len(filename) > 255:
                # 对于超过限制的文件名，采用md5替代
                filename = cm.get_md5(filename)
            output = os.path.join(self.output_dir, filename)
            with open(output, 'w') as fw:
                fcntl.flock(fw, fcntl.LOCK_EX)
                fw.write(content)
                fcntl.flock(fw, fcntl.LOCK_UN)
        if self.display_path:
            logger.info('All results for url: {} are saved in path: '
                        '{}'.format(self.site, self.output_dir))

    def pipe_process(self):
        """
        处理数据管道
        :return:
        """
        if not self.pipeline:
            # 没有传入管道，那么使用默认的存储方法
            self._save()
        else:
            # 遍历管道类中的所有以pipe_开头的方法，全部调用
            for method in dir(self.pipeline):
                if method.startswith('pipe_'):
                    func = getattr(self.pipeline, method)
                    if callable(func):
                        func(self.result_dict)

    def extract_links(self, url, page_content, page_text):
        """
        解析页面内链接
        :param url: 源url
        :param page_content: 页面内容
        :param page_text: 解码之后的页面内容
        :return:
        """
        if not page_content:
            return set()
        links = set()
        logger.info('Extract links from page: %s' % url)
        dom_tree = PyQuery(page_content)
        if dom_tree is None:
            logger.info('Get no dom tree for url: %s' % url)
            return links

        for ele in dom_tree('a'):
            if not 'href' in ele.attrib:
                continue
            href = ele.attrib['href']
            if href in ['/', '*']:
                continue
            if href.startswith('javascript') or href.startswith('mailto'):
                continue
            links.add(href)
            logger.info('Get link: %s' % href)

        for iframe in dom_tree('frame,iframe'):
            if not 'src' in iframe.attrib:
                continue
            iframe_src = iframe.attrib['src']
            if iframe_src is None or iframe_src.strip() in [
                "", "about:blank", "*"]:
                continue
            if "*" in iframe_src:
                continue
            # real_iframe_src = get_real_src(url, iframe_src)
            links.add(iframe_src)
            logger.info('Get link: %s' % iframe_src)
        # 使用正则匹配可能未解析到的url
        extra_urls = cm.match_url(page_text)
        for extra_url in extra_urls:
            links.add(extra_url)
        # 去掉不需要的后缀的链接
        links = filter(is_not_special_type_link, links)

        if self.level == 0:
            current_domain = cm.get_host_from_url(url)
            filter_func = lambda x: cm.get_host_from_url(x) == current_domain
        elif self.level == 1:
            current_sld = cm.get_sld(url)
            filter_func = lambda x: cm.get_sld(x) == current_sld
        elif self.level == 2:
            filter_func = lambda x: 1
        else:
            raise ValueError('The column "level" must in (0, 1, 2),'
                             ' but now is: {}'.format(self.level))
        links = {cm.validate_and_fill_url(url, link) for link in links}
        links = filter(filter_func, links)
        if not links:
            logger.info('No links in page: %s' % url)
        return links

    async def download_page(self, url):
        """
        下载单个页面
        :param url: 待下载url
        :return:
        """
        standard_url = cm.standard_url(url)
        if standard_url in self.has_crawled_pages:
            logger.info('The url has been crawled, '
                        'now skip it: {}'.format(url))
            return '', ''
        self.has_crawled_pages.append(standard_url)
        self.download_count += 1
        if self.splash:
            # 请求splash服务器
            rq_url = conf.SPLASH_RENDER
            rq_params = {
                'url': url,
                'image': conf.ENABLE_IMAGE,
                'timeout': conf.SPLASH_TIMEOUT
            }
            headers = {}
        else:
            rq_url = url
            rq_params = {}
            url_obj = parse.urlparse(rq_url)
            if self.count == 1:
                referer = cons.DEFAULT_REFERER
            else:
                referer = url_obj.scheme + url_obj.netloc
            if not self.user_agent:
                ua = UserAgent(use_cache_server=False, path=conf.FAKE_UA_DATA_PATH)
                user_agent = ua.random
            else:
                user_agent = self.user_agent

            headers = {
                'Referer': referer,
                'User-Agent': user_agent
            }
        try:
            if self.proxy:
                content, page_text = await request_with_proxy(
                    method='GET',
                    url=rq_url,
                    params=rq_params,
                    headers=headers
                )
            else:
                content, page_text = await aio_request(
                    method='GET',
                    url=rq_url,
                    params=rq_params,
                    headers=headers
                )
        except Exception as err:
            logger.warning('Download page content failed, '
                           'url: {}, error: {}'.format(url, err))
            return '', ''
        logger.info('Download successfully, url: {}'.format(url))
        self.success_count += 1
        return content, page_text

    async def crawl_in_one_loop(self, tmp_links, url, last_one=False):
        """
        单个url爬虫
        :param tmp_links:
        :param url:
        :param last_one: 是否为最后一个层级
        :return:
        """
        async with self.semaphore:
            content, page_text = await self.download_page(url)
            if not content:
                logger.info('Ignore blank page! The url: %s' % url)
                self.useless_page_count += 1
                return
            if self.ac.search(page_text) and len(page_text) < 1000:
                logger.info('Ignore useless page! The url: %s' % url)
                self.useless_page_count += 1
                return
            if self.decode:
                self.result_dict['results'][url] = page_text
            else:
                self.result_dict['results'][url] = content
            if not last_one:
                # 最后一个层级不去解析页面内链接
                links = self.extract_links(url, content, page_text)
                if links:
                    for link in links:
                        tmp_links.add(link)

            # 处理数据管道
            self.pipe_process()
            # 保存完毕之后清空缓存结果，减少内存开销
            self.init_result_cache()

    def crawl(self, urls):
        """
        爬取一个站点下的多个链接页面
        :param urls: url列表
        :return:
        """
        # 已爬取深度计数加1
        self.count += 1
        # 用于递归传递url
        tmp_links = set()
        tasks = []
        last_one = False
        if self.count > self.max_depth:
            last_one = True
        for url in urls:
            tasks.append(self.crawl_in_one_loop(tmp_links, url, last_one))
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(asyncio.gather(*tasks))

        if tmp_links:
            self.crawl(tmp_links)

    def run(self):
        """运行"""
        self.crawl([self.site])
        queue.put((self.download_count, self.success_count, self.useless_page_count))


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