"""
Author: lt
Date: 2019-11-05
Desc: 终端执行入口
"""
import asyncio
import ctypes
import optparse
import os
import re
import time
import traceback

from datetime import date
from loguru import logger
from multiprocessing import Pool
from multiprocessing import Queue
from queue import Empty

import common as cm
import config as conf

from daemon import Daemon
from spider import Spider

queue = Queue()
# os.chdir(sys.path[0])
script_path = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PROCESSES = 8


def parse_args():
    """解析命令行输入"""
    usage = 'Usage: \n\tpython get_archival_info.py \n\t[-i] <input_path> \n\t[-o] ' \
            '<output dir> \n\t[-c] <concurrent limit> \n\t[-p] ' \
            '<processes num> \n\t[-d] <max depth each site>' \
            '\n\t[-D] <run as daemon> \n\t[-u] <choose one or more urls to crawl> ' \
            '\n\t[-L] <crawl level> \n\t[-S] <whether to use splash> ' \
            '\n\t[-P] <whether to use proxy pool> \n\t[-B] \n\t[start] | restart | stop'
    parser = optparse.OptionParser(usage=usage)
    input_help_str = 'The path of file which contains ' \
                     'the list of sites to be crawled'
    parser.add_option(
        '-i', '--input',
        type='str',
        dest='input',
        help=input_help_str
    )
    output_help_str = 'The base output dir that stores all of the crawled results'
    parser.add_option(
        '-o', '--output',
        type='str',
        dest='output',
        help=output_help_str
    )
    concurrent_help_str = 'Limit the number of concurrency of a single process'
    parser.add_option(
        '-c', '--concurrent',
        type='int',
        dest='concurrent',
        help=concurrent_help_str
    )
    process_help_str = 'Number of processes started.' \
                       'It only makes sense when you crawl multiple urls'
    parser.add_option(
        '-p', '--processes',
        type='int',
        dest='processes',
        help=process_help_str
    )
    depth_help_str = 'Limit the max depth of pages while crawling'
    parser.add_option(
        '-d', '--depth',
        type='int',
        dest='depth',
        help=depth_help_str
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
    user_agent_help_str = 'Specific the access user-agent'
    parser.add_option(
        '-U', '--user_agent',
        type='str',
        dest='user_agent',
        help=user_agent_help_str
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
                     ' When you select this option, you will use the proxy to access the target.' \
                     ' But do not forget to change configuration'
    parser.add_option(
        '-P', '--proxy',
        action='store_true',
        dest='proxy',
        help=proxy_help_str
    )
    bs64_help_str = 'Whether to use base64 encode url as the file names'
    parser.add_option(
        '-B', '--bs64',
        action='store_true',
        dest='bs64',
        help=bs64_help_str
    )

    options, args = parser.parse_args()
    return options, args


def crawl_one_site(url, base_output_dir, max_depth,
                   concurrent_limit, level=0,
                   splash=False, proxy=False,
                   bs64encode_filename=False,
                   user_agent=None):
    """递归下载一个站点"""
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(1, 15)
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
                 level=0, splash=False, proxy=False,
                 bs64encode_filename=False, processes=None,
                 user_agent=None):
        self.urls = urls
        self.base_output_dir = base_output_dir
        self.max_depth = max_depth
        self.concurrent_limit = concurrent_limit
        self.level = level
        self.splash = splash
        self.proxy = proxy
        self.bs64encode_filename = bs64encode_filename
        self.processes = processes
        self.user_agent = user_agent

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
        if not self.processes:
            self.processes = DEFAULT_PROCESSES
        pool = Pool(self.processes)
        for url in self.urls:
            pool.apply_async(
                crawl_one_site,
                args=(url, self.base_output_dir, self.max_depth,
                      self.concurrent_limit, self.level,
                      self.splash, self.proxy, self.bs64encode_filename,
                      self.user_agent)
            )
        pool.close()
        pool.join()

        total_count = 0
        success_count = 0
        useless_count = 0
        while True:
            try:
                count_tuple = queue.get_nowait()
                total_count += count_tuple[0]
                success_count += count_tuple[1]
                useless_count += count_tuple[2]
            except Empty:
                break
        end_time = time.time()
        expense_time = end_time - start_time
        speed = total_count / expense_time
        logger.info(
            'The base output dir is: {}, you can find all'
            ' results from it by domain'.format(
                os.path.abspath(self.base_output_dir))
        )
        logger.info(
            "Crawl finished, total expense time: {}s, "
            "total download: {}, success: {}, speed: {}/s".format(
                end_time - start_time, total_count,
                success_count, speed
            )
        )
        # 结束之后去掉pid文件
        if os.path.isfile(self._pidfile):
            os.remove(self._pidfile)


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


def main():
    """
    主函数
    :return:
    """
    options, args = parse_args()
    input_path = conf.DEFAULT_INPUT_PATH
    base_output_dir = conf.DEFAULT_OUTPUT_DIR
    concurrent_limit = conf.CONCURRENT_LIMIT
    max_depth = conf.MAX_DEPTH
    level = conf.LEVEL
    input_url = ''
    user_agent = None
    processes = conf.PROCESS_NUM

    if options.concurrent is not None:
        concurrent_limit = options.concurrent
    if options.depth is not None:
        max_depth = options.depth
    if options.input is not None:
        input_path = options.input
    if options.output is not None:
        base_output_dir = options.output
    if options.processes:
        processes = options.processes
    if options.url is not None:
        input_url = options.url
    if options.level is not None:
        level = options.level
    if options.user_agent is not None:
        user_agent = options.user_agent
    daemon = options.daemon
    use_splash = options.splash
    use_proxy = options.proxy
    bs64 = options.bs64

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
        proxy=use_proxy,
        bs64encode_filename=bs64,
        processes=processes,
        user_agent=user_agent
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
