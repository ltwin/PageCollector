"""
命令交互
"""
import click
import json
import os

from bson import ObjectId
from json import JSONDecodeError
from traceback import format_exc

import config as conf

from tasks.spider_task import crawler
from db_utils.mongo import MongoDB
from db_utils.mongo import MongoFile
from db_utils import db_settings as dbs


LEVEL_HELP_STR = 'The option "level" represents the crawler filtering level,' \
                 ' you can choose the number: 0(only contains the same domain links),' \
                 ' 1(contains the same links for secondary domains),' \
                 ' 2(contains all of links)'
SPLASH_HELP_STR = 'You can add this option if you have a splash service.' \
                  ' When you select this option, you will use it to render the page.' \
                  'But do not forget to change configuration'
PROXY_HELP_STR = 'You can add this option if you have a proxy service.' \
                 ' When you select this option, you will use the proxy to access the target.' \
                 ' But do not forget to change configuration'


@click.group()
def cli():
    pass


def start():
    """start some workers"""
    pass


@cli.command('submit')
@click.option('--source', '-s', type=str, help=
'Specify the file path contains all of the urls which need to be crawled')
@click.option('--url', '-u', multiple=True)
@click.option('--concurrent_limit', type=int,
              help='Limit the number of concurrency of a single process')
@click.option('--depth', '-d', type=int,
              help='Limit the max depth of pages while crawling')
@click.option('--level', '-L', type=int, help=LEVEL_HELP_STR)
@click.option('--user_agent', '-U', type=str,
              help='Specific the access user-agent')
@click.option('--splash', '-S', type=bool, help=SPLASH_HELP_STR)
@click.option('--proxy', '-P', type=bool, help=PROXY_HELP_STR)
def submit(source, url, concurrent_limit, depth,
           user_agent, level, splash, proxy):
    if not any([source, url]):
        raise ValueError(
            'You should at least input parameter "source" or "url"!')
    urls = []
    tasks = []
    if source:
        with open(source, 'r') as fr:
            items = fr.readlines()
            items = [item.strip().strip('\r').strip('\n') for item in items]
            for item in items:
                item = item.strip().strip('\r').strip('\n')
                try:
                    url_dict = json.loads(item)
                    tasks.append(url_dict)
                except (ValueError, JSONDecodeError):
                    urls.append(item)
    if url:
        for one_url in url:
            urls.append(one_url)
    for url in urls:
        task = {'url': url}
        if concurrent_limit is not None:
            task.update({'concurrent_limit': concurrent_limit})
        if depth is not None:
            task.update({'max_depth': depth})
        if level is not None:
            task.update({'level': level})
        if user_agent is not None:
            task.update({'user_agent': user_agent})
        if splash is not None:
            task.update({'use_splash': splash})
        if proxy is not None:
            task.update({'use_proxy': proxy})
        tasks.append(task)
    for task in tasks:
        crawler.send(task)


@cli.command('export')
@click.option('--task', '-t', type=str)
@click.option('--url', '-u', type=str)
@click.option('--output','-o', type=str)
def export(task, url, output):
    if not any([task, url]):
        print('You should at least input one of params "task" or "url"!')
        return
    mongo = MongoDB(conf.MONGO_URI)
    mongo_file = MongoFile(conf.MONGO_URI)
    search_filter = {}
    if task:
        search_filter.update({'task': task})
    if url:
        search_filter.update({'url': url})
    results, _ = mongo.find_many(
        coll_name=dbs.RESULT_TB,
        sfilter=search_filter,
        sort_str='update_time'
    )
    if not results:
        print('No result found!')
    export_list = []
    if url:
        # 传入url表示只需要导出该url的一条事件
        export_list.append(results[0])
    else:
        export_list.extend(results)
    for result in results:
        ref_content_id = result.get('ref_content_id')
        url = result.get('url', 'null')
        filename = url.replace('/', '{').replace(
            ':', '}').replace('*', '[').replace('?', '^')
        try:
            ref_content_id = ObjectId(ref_content_id)
            data, info = mongo_file.get_file_by_id(
                dbs.CONTENT_TB, ref_content_id)
        except Exception:
            print('Error occurred while getting content!'
                  ' The error: %s' % format_exc())
            continue
        if isinstance(data, bytes):
            data = data.decode()
        if not output:
            print(data)
            return
        if not os.path.isdir(output):
            os.system('mkdir -p %s' % output)
        with open(os.path.join(output, filename), 'w') as fw:
            fw.write(data)


@click.option('--task', '-t', type=str)
@click.option('--url', '-u', type=str)
def delete_result(task, url):
    pass


if __name__ == '__main__':
    cli()
