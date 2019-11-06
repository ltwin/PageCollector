"""
Author: lt
Date: 2019-11-05
Desc: 数据管道
"""
import os

from bson import ObjectId
from datetime import datetime
from loguru import logger

import config as conf

from common import get_md5
from db_utils.mongo import MongoDB
from db_utils.mongo import MongoFile
from db_utils import db_settings as ds


class Pipeline:
    """
    自定义数据管道，需自行编写处理方法，所有以pipe_开头的方法将被执行
    执行方法参数至少有一个，第一个参数将会被作为爬虫结果传输入口
    注意：当使用cli命令行调用时，管道不会生效
    数据格式为：
        {
            "task": "http://www.example.com",
            "results": {
                "http://www.example.com/a": "aaa",
                "http://www.example.com/b": "bbb"
            }
        }
    """

    def pipe_save2mongo(self, data):
        """
        将数据存入mongo
        :return:
        """
        mongo_db = MongoDB(conf.MONGO_URI)
        mongo_file = MongoFile(conf.MONGO_URI)
        task = data['task']
        for url, content in data['results'].items():
            # 首先检查是否已经存在
            exists_result = mongo_db.find_one(
                coll_name=ds.RESULT_TB,
                sfilter={'task': task, 'url': url}
            )
            if exists_result:
                # 若存在，则删除原有的结果内容
                mongo_file.remove_file(
                    coll_name=ds.CONTENT_TB,
                    file_id=exists_result['ref_content_id']
                )

            file_id = mongo_file.insert_by_data(
                coll_name=ds.CONTENT_TB,
                key=get_md5(url),
                data=content
            )
            mongo_db.update_many(
                coll_name=ds.RESULT_TB,
                sfilter={'task': task, 'url': url},
                data={
                    'task': task,
                    'url': url,
                    'ref_content_id': ObjectId(file_id),
                    'update_time': datetime.now()
                },
                upsert=True
            )
            logger.info('Save result successfully! The url: {}'.format(url))
