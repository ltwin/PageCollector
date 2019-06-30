"""
Author: lt
Date: 2019-06-19
Description: 根据site下载页面，可定义层级深度，只是用于收集页面，
    出于效率的考虑，因此没有使用浏览器模拟，无法处理js动态生成的文本
"""

import asyncio
import fcntl
import optparse
import os
import re
import sys
import time
import traceback

from datetime import date
from loguru import logger
from multiprocessing import Pool
from multiprocessing import Queue
from multiprocessing.queues import Empty
from pyquery import PyQuery
from random import randint
from urllib import parse

import common as cm
import config as conf
import constansts as cons
from daemon import Daemon

from proxy_utils import aio_request
from proxy_utils import request_with_proxy

queue = Queue()
os.chdir(sys.path[0])
script_path = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    """解析命令行输入"""
    usage = 'Usage: \n\tpython get_archival_info.py \n\t[-i] <input_path> \n\t[-o] ' \
            '<output dir> \n\t[-l] <concurrent limit> \n\t[-d] <max depth each site>' \
            '\n\t[-D] <run as daemon> \n\t[-u] <choose one or more urls to crawl> ' \
            '\n\t[-L] <crawl level> \n\t[-S] <whether to use splash> ' \
            '\n\t[-P] <whether to use proxy pool> \n\t[start] | restart | stop'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        '-i', '--input',
        type='str',
        dest='input'
    )
    parser.add_option(
        '-o', '--output',
        type='str',
        dest='output'
    )
    parser.add_option(
        '-l', '--concurrent',
        type='int',
        dest='concurrent'
    )
    parser.add_option(
        '-d', '--depth',
        type='int',
        dest='depth'
    )
    parser.add_option(
        '-D', '--daemon',
        action='store_true',
        dest='daemon'
    )
    url_help_str = 'You can input one or more urls to crawl, ' \
                   'multiple urls need to be separated by commas, ' \
                   'examples: "www.a.com" or "www.a.com, www.b.com"'
    parser.add_option(
        '-u', '--url',
        type='str',
        dest='url',
        help=url_help_str
    )
    level_help_str = 'The option "level" represents the crawler filtering level,' \
                     ' you can choose the number: 0(only contains the same domain links),' \
                     ' 1(contains the same links for secondary domains),' \
                     ' 2(contains all of links)'
    parser.add_option(
        '-L', '--level',
        type='int',
        dest='level',
        help=level_help_str
    )
    splash_help_str = 'You can add this option if you have a splash service.' \
                      ' When you select this option, you will use it to render the page.' \
                      'But do not forget to change configuration'
    parser.add_option(
        '-S', '--splash',
        action='store_true',
        dest='splash',
        help=splash_help_str
    )
    proxy_help_str = 'You can add this option if you have a proxy service.' \
                     ' When you select this option, uou will use the proxy to access the target.' \
                     ' But do not forget to change configuration'
    parser.add_option(
        '-P', '--proxy',
        action='store_true',
        dest='proxy',
        help=proxy_help_str
    )

    options, args = parser.parse_args()
    return options, args


def validate_url(domain):
    """
    检验domain是否合法
    :param domain: www.sangfor.com.cn
    :return:
    """
    if not isinstance(domain, str):
        logger.warning('Invalid domain input, it must be string type,'
                       ' but now is: %s' % type(domain))
        return False
    if not re.match('.+\..+', domain):
        logger.info('Invalid domain: %s' % domain)
        return False
    return True


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


def parse_line(path):
    """
    解析存放待搜索域名列表的文件
    :param path: 文件路径
    :return:
    """
    ret = []
    with open(path, 'r') as fr:
        lines = fr.readlines()
    for line in lines:
        line = line.strip('\n').strip('\r')
        if validate_url(line):
            ret.append(line)
    return ret


def is_special_type_link(link):
    """
    该链接是否指向特定后缀名的资源
    :param link
    :type link: str
    """
    if link.endswith('download/app'):
        return True
    link_extension = link.split('.')[-1]
    return link_extension in cons.IGNORED_EXTENSIONS


class Spider(object):
    """
    递归爬取批量的网站的多个子页面
    """

    def __init__(self, site, output_dir, semaphore,
                 max_depth=2, decode=True, display_path=True,
                 level=0, splash=False, proxy=False):
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
        self.count = 0
        self.download_count = 0
        self.success_count = 0
        self.result_dict = {}
        self.has_crawled_pages = []

    def _save(self):
        """
        保存页面到文件
        :return:
        """
        for page, content in self.result_dict.items():
            filename = page.replace('/', '{').replace(
                ':', '}').replace('*', '[').replace('?', '^') + '.html'
            # 文件名不得长于linux长度限制
            if len(filename) > 255:
                # 对于超过限制的文件名，采用md5替代
                filename = cm.get_md5(filename) + '.html'
            output = os.path.join(self.output_dir, filename)
            with open(output, 'w') as fw:
                fcntl.flock(fw, fcntl.LOCK_EX)
                fw.write(content)
                fcntl.flock(fw, fcntl.LOCK_UN)
        if self.display_path:
            logger.info('All results for url: {} are saved in path: '
                        '{}'.format(self.site, self.output_dir))

    def extract_links(self, url, page_content):
        """
        解析页面内链接
        :param url: 源url
        :param page_content: 页面内容
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
            if is_special_type_link(href):
                logger.debug(['specail type:', href.encode('utf-8')])
                continue
            # real_src = get_real_src(home_url, href)
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
            user_agent = cons.USER_AGENT[randint(0, len(cons.USER_AGENT) - 1)]
            headers = {'User-Agent': user_agent}
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

    async def get_start_page(self):
        """
        获取起始页面及其页面中的url
        :return:
        """
        content, page_text = await self.download_page(self.site)
        if not content:
            return []
        if self.decode:
            self.result_dict[self.site] = page_text
        else:
            self.result_dict[self.site] = content
        self._save()
        self.result_dict = {}
        logger.info('Get start page for site: %s successfully!' % self.site)
        return self.extract_links(self.site, content)

    async def crawl_in_one_loop(self, tmp_links, url):
        """
        单个url爬虫
        :param tmp_links:
        :param url:
        :return:
        """
        async with self.semaphore:
            content, page_text = await self.download_page(url)
            if not content:
                return
            links = self.extract_links(url, content)
            if links:
                for link in links:
                    link_content, link_page_text = await self.download_page(link)
                    if self.decode:
                        self.result_dict[link] = link_page_text
                    else:
                        self.result_dict[link] = link_content
                    tmp_links.add(link)

            # 保存页面到文件
            self._save()
            # 保存完毕之后清空缓存结果，减少内存开销
            self.result_dict = {}

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
        for url in urls:
            tasks.append(self.crawl_in_one_loop(tmp_links, url))
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(asyncio.gather(*tasks))

        if tmp_links and self.count <= self.max_depth:
            self.crawl(tmp_links)

    def run(self):
        """运行"""
        urls_in_start_page = self.get_start_page()
        event_loop = asyncio.get_event_loop()
        results = event_loop.run_until_complete(asyncio.gather(urls_in_start_page))
        result = results[0]
        if self.max_depth > 0:
            self.crawl(result)
        queue.put((self.download_count, self.success_count))


def crawl_one_site(url, base_output_dir, max_depth,
                   concurrent_limit, level=0,
                   splash=False, proxy=False):
    """递归下载一个站点"""
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
        proxy=proxy
    )
    try:
        spider.run()
    except:
        logger.error('Error occurred while running: '
                     '{}'.format(traceback.format_exc()))


class Worker(Daemon):
    """
    工作者
    """

    def __init__(self, urls, base_output_dir,
                 max_depth, concurrent_limit,
                 work_dir=script_path, daemon=False,
                 level=0, splash=False, proxy=False):
        self.urls = urls
        self.base_output_dir = base_output_dir
        self.max_depth = max_depth
        self.concurrent_limit = concurrent_limit
        self.level = level
        self.splash = splash
        self.proxy = proxy
        pid_file = os.path.join(conf.PID_DIR, 'page_collect.pid')
        super(Worker, self).__init__(pid_file, work_dir, daemon=daemon)

    def _run(self):
        """
        入口
        :return:
        """
        start_time = time.time()
        today_str = str(date.today()).replace('-', '')
        log_path = os.path.join(conf.LOG_DIR, ''.join(['page_collect_', today_str, '.log']))
        logger.add(
            sink=log_path,
            level='INFO',
            enqueue=True,
            rotation='200 MB'
        )
        logger.info('Start crawler, the url list: %s' % self.urls)
        pool = Pool(conf.PROCESS_NUM)
        for url in self.urls:
            pool.apply_async(
                crawl_one_site,
                args=(url, self.base_output_dir, self.max_depth,
                      self.concurrent_limit, self.level,
                      self.splash, self.proxy)
            )
        pool.close()
        pool.join()

        total_count = 0
        success_count = 0
        while True:
            try:
                count_tuple = queue.get_nowait()
                total_count += count_tuple[0]
                success_count += count_tuple[-1]
            except Empty:
                break
        end_time = time.time()
        expense_time = end_time - start_time
        speed = total_count / expense_time
        logger.info('The base output dir is: {}, you can find all'
                    ' results from it by domain'.format(os.path.abspath(self.base_output_dir)))
        logger.info("Crawl finished, total expense time: {}s, "
                    "total download: {}, success: {}, speed: "
                    "{}".format(end_time - start_time, total_count, success_count, speed))
        # 结束之后去掉pid文件
        if os.path.isfile(self._pidfile):
            os.remove(self._pidfile)


def main():
    """
    主函数
    :return:
    """
    options, args = parse_args()
    daemon = conf.DAEMON
    input_path = conf.DEFAULT_INPUT_PATH
    base_output_dir = conf.DEFAULT_OUTPUT_DIR
    concurrent_limit = conf.CONCURRENT_LIMIT
    max_depth = conf.MAX_DEPTH
    level = conf.LEVEL
    input_url = ''

    if options.concurrent is not None:
        concurrent_limit = options.concurrent
    if options.depth is not None:
        max_depth = options.depth
    if options.input is not None:
        input_path = options.input
    if options.output is not None:
        base_output_dir = options.output
    if options.daemon is not None:
        daemon = options.daemon
    if options.url is not None:
        input_url = options.url
    if options.level is not None:
        level = options.level
    use_splash = options.splash
    use_proxy = options.proxy


    if input_url:
        url_list = [url.replace(' ', '') for url in input_url.split(',')]
    else:
        url_list = parse_line(input_path)
    worker = Worker(
        urls=url_list,
        base_output_dir=base_output_dir,
        max_depth=max_depth,
        concurrent_limit=concurrent_limit,
        daemon=daemon,
        level=level,
        splash=use_splash,
        proxy=use_proxy
    )

    if not args:
        print('------start page_collect successfully------')
        worker.start()
    elif len(args) == 1:
        if args[0] == 'start':
            print('------start page_collect successfully------')
            worker.start()
        elif args[0] == 'stop':
            print('------stop page_collect successfully------')
            worker.stop()
        elif args[0] == 'restart':
            print('------restart page_collect successfully------')
        else:
            raise ValueError('Invalid status args!')
    else:
        raise ValueError('Too many args input!')


if __name__ == '__main__':
    main()
