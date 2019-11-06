"""
Author: lt
CreateDate: 2019-07-23
UpdateDate: 2019-07-23
Interpreter: Python3.6+
Description: MongoDB文档操作封装
"""

import pymongo
import traceback

from asyncio import coroutine
from bson import ObjectId
from gridfs import GridFS
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from db_utils import db_settings as ds
from db_utils import exceptions as exc


class ConnectBase:
    """
    MongoDB初始化连接基类
    """

    def __init__(self, uri, db_name=ds.DB):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.log_prefix = ''

        self._connect_db()
        self.change_to_db()

    def _connect_db(self):
        """
        连接数据库
        :return:
        """
        try:
            self.client = MongoClient(self.uri)
        except PyMongoError as err:
            logger.error(
                '{}Connect mongodb failed! Error: '
                '{}'.format(self.log_prefix, err)
            )

    def change_to_db(self, db_name=None):
        if not self.client:
            return
        changed_db = db_name if db_name else self.db_name
        try:
            self.db = self.client.get_database(name=changed_db)
        except PyMongoError as err:
            logger.error(
                '{}Change to database "{}" failed, error: '
                '{}'.format(self.log_prefix, self.db_name, err)
            )

    def disconnect_db(self):
        if self.client:
            self.client.close()

    def __del__(self):
        """
        对象销毁时断开MongoDB连接
        :return:
        """
        self.disconnect_db()
        logger.debug('Disconnect mongodb client.')


class MongoDB(ConnectBase):
    """
    封装MongoDB基础操作类
    """

    def __init__(self, uri, db_name=ds.DB):
        self.log_prefix = '[DB][Mongo]'
        self.default_callback = lambda x: x
        super(MongoDB, self).__init__(uri=uri, db_name=db_name)

    def _before_run(func):
        def inner(self, *args, **kwargs):
            if not self.db:
                return False
            return func(self, *args, **kwargs)
        return inner

    def run_command(self, coll_name, command_type,
                    callback=None, *args, **kwargs):
        """
        通用，执行数据库操作命令
        :param coll_name: 集合名称
        :param command_type: 指定命令
        :param callback: 回调函数
        :return:
        """
        coll = self.db.get_collection(name=coll_name)
        command = getattr(coll, command_type)
        if callback:
            return callback(command(*args, **kwargs))
        command(*args, **kwargs)

    @_before_run
    def insert_one(self, coll_name, data, has_return=True):
        """
        插入单条数据
        :param coll_name: collection name
        :param data: 需要插入的数据
        :param has_return: 需要返回结果
        :return:
        """
        try:
            callback = self.default_callback if has_return else None
            insert_ret = self.run_command(
                coll_name=coll_name,
                command_type='insert_one',
                callback=callback,
                document=data
            )
        except Exception:
            raise exc.InsertException(
                '{}Insert data to database "{}" failed! Error: '
                '{}'.format(self.log_prefix, coll_name, traceback.format_exc())
            )
        if insert_ret:
            return insert_ret.inserted_id

    @_before_run
    def insert_many(self, coll_name, data, has_return=True):
        """
        插入多条数据
        :param coll_name: collection name
        :param data: 多条插入文档
        :param has_return
        :return:
        """
        try:
            callback = self.default_callback if has_return else None
            insert_ret = self.run_command(
                coll_name, 'insert_many', callback, data)
        except Exception:
            raise exc.InsertException(
                '{}Insert many data to database "{}" failed! Error: '
                '{}'.format(self.log_prefix, coll_name, traceback.format_exc())
            )
        return insert_ret.inserted_ids

    @_before_run
    def update_many(self, coll_name, sfilter, data,
                    byset=True,
                    upsert=False,
                    ignore_not_exist_error=False,
                    lock=False,
                    lock_name=None,
                    lock_value=None,
                    repl=False,
                    repl_key='_id',
                    has_return=True):
        """
        更新数据
        :param coll_name: collection name
        :type coll_name: str
        :param sfilter: 查询条件
        :type sfilter: dict
        :param data: 更新数据
        :type data: dict
        :param byset: 以单个字段更新方式
        :type byset: bool
        :param upsert: 是否在更新数据时判断数据是否存在并决定是否插入新数据
        :type upsert: bool
        :param ignore_not_exist_error: 是否忽略数据不存在的异常
        :type ignore_not_exist_error: bool
        :param lock: 是否以乐观锁的方式启动
        :type lock: bool
        :param lock_name: 锁的字段名
        :type lock_name: str
        :param lock_value: 传入的锁的值
        :type lock_value: int
        :param repl: 是否为分片的表
        :type repl: bool
        :param repl_key: 片键
        :type repl_key: str
        :param has_return: 是否需要获取返回值
        :type has_return: bool
        :return:
        """
        callback = self.default_callback if has_return else None
        if lock:
            if lock_name is None or lock_value is None:
                raise ValueError(
                    'You should input lock_name and '
                    'lock_value while updating in lock mode'
                )
            res = self.find_one(
                coll_name=coll_name,
                sfilter=sfilter
            )
            if not res:
                if ignore_not_exist_error:
                    # 忽略数据不存在的异常则直接返回True
                    return True
                raise exc.OperateNotExistsDataException(
                    'The data updated not exists!'
                )
            version = res.get(lock_name, 0)
            if lock_value < version:
                raise exc.OverdueOperationException
            data.update({lock_name: (version + 1)})
        try:
            if byset:
                data = {'$set': data}
            if repl:
                # 对于分片的表，应该先查出对应的分片
                update_count = 0
                repl_key_results, _ = self.find_many(
                    coll_name=coll_name,
                    sfilter=sfilter,
                    projection={repl_key: 1}
                )
                for repl_key_result in repl_key_results:
                    repl_key_value = repl_key_result[repl_key]
                    sfilter.update({repl_key: repl_key_value})
                    ret = self.run_command(
                        coll_name=coll_name,
                        command_type='update_many',
                        callback=callback,
                        filter=sfilter,
                        update=data,
                        upsert=upsert
                    )
                    if ret.modified_count:
                        update_count += 1
            else:
                ret = self.run_command(
                    coll_name,
                    'update_many',
                    callback=callback,
                    filter=sfilter,
                    update=data,
                    upsert=upsert
                )
                update_count = ret.modified_count
        except Exception:
            raise exc.UpdateException(
                '{}Update data from database "{}" failed! Error: '
                '{}'.format(self.log_prefix, coll_name, traceback.format_exc())
            )
        if update_count:
            return True
        elif not upsert and not ignore_not_exist_error:
            # 在upsert模式下，就算数据不存在也没问题
            raise exc.OperateNotExistsDataException(
                'The data updated not exists!'
            )
        else:
            return True

    @_before_run
    def find_one(self, coll_name, sfilter, aggregate=False):
        """
        查询单条数据
        :param coll_name: collection name
        :param sfilter: 查询条件
        :param aggregate: 是否为聚合操作
        :return:
        """
        callback = self.default_callback
        try:
            if aggregate:
                ret = self.run_command(
                    coll_name, 'aggregate', callback, sfilter)
            else:
                ret = self.run_command(
                    coll_name, 'find_one', callback, sfilter)
            return ret
        except Exception:
            raise exc.FindException(
                '{}Find data from database "{}" failed! Error: {}'.format(
                    self.log_prefix, coll_name, traceback.format_exc())
            )

    @_before_run
    def find_many(self, coll_name,
                  offset=None,
                  limit=None,
                  sfilter=None,
                  aggregate=False,
                  sort_str=None,
                  projection=None):
        """
        分页查询所有数据
        :param coll_name:collection name
        :type coll_name: str
        :param offset: 偏移量，为0则表示查询全部
        :type offset: int
        :param limit: 每页条数
        :type limit: int
        :param aggregate: 是否为聚合操作
        :type aggregate: bool
        :param sort_str: 排序依据
        :type sort_str: str
        :param projection: 决定输出哪些字段
        :type projection: dict
        :return:
        """
        callback = self.default_callback
        try:
            if aggregate:
                ret = list(
                    self.run_command(coll_name, 'aggregate', callback, sfilter)
                )
                leng = len(ret)
                if offset:
                    ret = ret[offset:: 1]
                if limit:
                    ret = ret[0: limit: 1]
            else:
                # pymongo是在list转换的时候才会真正查询数据库，在此之前只是一个游标
                ret = self.run_command(
                    coll_name, 'find', callback, sfilter, projection=projection)
                if isinstance(offset, int):
                    ret = ret.skip(offset)
                if isinstance(limit, int):
                    ret = ret.limit(limit)
                if isinstance(sort_str, str):
                    ret = ret.sort([(sort_str, pymongo.DESCENDING)])
                leng = self.get_count(coll_name, sfilter)
            return list(ret), leng
        except Exception:
            raise exc.FindException(
                '{}Find data from collection "{}" failed! Error: {}'.format(
                    self.log_prefix, coll_name, traceback.format_exc())
            )

    @_before_run
    def get_count(self, coll_name, sfilter):
        """
        获取记录个数
        :param coll_name:
        :param sfilter:
        :return:
        """
        callback = self.default_callback
        try:
            count = self.run_command(
                coll_name, 'count', callback, filter=sfilter)
        except Exception:
            raise exc.FindException(
                '{}Get data count from collection "{}" failed! Error: '
                '{}'.format(self.log_prefix, coll_name, traceback.format_exc())
            )
        return count

    @_before_run
    def delete_many(self, coll_name, sfilter,
                    ignore_not_exist_error=False,
                    has_return=True):
        """
        删除数据
        :param coll_name: 数据库集合名
        :type coll_name: str
        :param sfilter: 查询条件
        :type sfilter: dict
        :param ignore_not_exist_error: 是否忽略数据不存在的异常
        :type ignore_not_exist_error: bool
        :param has_return
        :return:
        """
        callback = self.default_callback if has_return else None
        try:
            ret = self.run_command(
                coll_name, 'delete_many', callback, sfilter)
            if ret.deleted_count:
                return True
            elif not ignore_not_exist_error:
                raise exc.OperateNotExistsDataException(
                    'The data deleted not exists!'
                )
            else:
                return True
        except Exception:
            raise exc.DeleteException(
                '{}Delete data from database "{}" failed! Error: '
                '{}'.format(self.log_prefix, coll_name, traceback.format_exc())
            )


# TODO 未完成，暂不使用
class AsyncMongo(MongoDB):
    """
    异步MongoDB操作类
    """

    def __init__(self, uri, db_name=ds.DB):
        self.__change_to_coroutine()
        super(AsyncMongo, self).__init__(uri, db_name=db_name)

    def _connect_db(self):
        """
        连接数据库
        :return:
        """
        try:
            self.client = AsyncIOMotorClient(self.uri)
        except Exception as err:
            logger.error('Connect mongodb failed! Error: %s' % err)

    async def __run_command(self, coll_name, command_type,
                    callback=None, *args, **kwargs):
        coll = self.db.get_collection(name=coll_name)
        command = getattr(coll, command_type)
        if callback:
            run_result = callback(command(*args, **kwargs))
            if hasattr(run_result, '__await__'):
                return await run_result
            return run_result
        command(*args, **kwargs)

    def run_command(self, coll_name, command_type,
                    callback=None, *args, **kwargs):
        return

    def __change_to_coroutine(self):
        self.find_one = coroutine(self.find_one)
        self.find_many = coroutine(self.find_many)
        self.update_many = coroutine(self.update_many)
        self.insert_one = coroutine(self.insert_one)
        self.insert_many = coroutine(self.insert_many)
        self.delete_many = coroutine(self.delete_many)
        self.get_count = coroutine(self.get_count)


class MongoFile(ConnectBase):
    """
    MongoDB文件操作类
    """

    def __init__(self, uri, db_name=ds.DB):
        self.log_prefix = '[DB][GridFs]'
        super(MongoFile, self).__init__(uri=uri, db_name=db_name)

    def insert_by_path(self, coll_name, path):
        """
        插入文件
        :param path: 文件路径
        :param coll_name: 表单名
        :return: 成功返回id+报告名，失败返回None
        """
        try:
            fs = GridFS(self.db, coll_name)
            with open(path) as fp:
                file_data = fp.read()
                file_id = fs.put(file_data, filename=path)
        except Exception:
            raise exc.InsertException(
                '{}Store file to "{}" failed! Path: {}, error: {}'.format(
                    self.log_prefix, coll_name, path, traceback.format_exc())
            )
        return file_id

    def insert_by_data(self, coll_name, key, data):
        """
        插入文件
        :return: 成功返回id+报告名，失败返回None
        """
        try:
            fs = GridFS(self.db, coll_name)
            if not isinstance(data, bytes):
                data = data.encode('utf-8')
            file_id = fs.put(data, filename=key)
        except Exception:
            raise exc.InsertException(
                '{}Store file to "{}" failed! Filename: {}, error: {}'.format(
                    self.log_prefix, coll_name, key, traceback.format_exc())
            )
        return file_id

    def get_file_by_id(self, coll_name, file_id):
        """
        根据ObjectId从gridFS获取文件
        :param coll_name: 集合名
        :param file_id: 文件唯一ID
        :return: 文件数据流和文件信息
        """
        try:
            fs = GridFS(self.db, coll_name)
            gf = fs.get(ObjectId(file_id))
            if not gf:
                return None
            data = gf.read()
            info = {
                "chunk_size": gf.chunk_size,
                "metadata": gf.metadata,
                "length": gf.length,
                "upload_data": gf.upload_date,
                "name": gf.name,
                "content-type": gf.content_type
            }
        except Exception:
            raise exc.FindException(
                '{}Get file from "{}" failed! _id: {}, error: {}'.format(
                    self.log_prefix, coll_name, file_id, traceback.format_exc())
            )
        return data, info

    def get_file_by_name(self, coll_name, name):
        """
        根据文件名从gridFS获取文件
        :param coll_name:
        :param name:
        :return:
        """
        try:
            fs = GridFS(self.db, coll_name)
            gf = fs.find({'name': name})
            if not gf:
                return None
            data = gf.read()
            info = {
                "chunk_size": gf.chunk_size,
                "metadata": gf.metadata,
                "length": gf.length,
                "upload_data": gf.upload_date,
                "name": gf.name,
                "content-type": gf.content_type
            }
        except Exception:
            raise exc.FindException(
                '{}Get file by name from "{}" failed! Name: {}, error: '
                '{}'.format(
                    self.log_prefix, coll_name, name, traceback.format_exc())
            )
        return data, info

    def remove_file(self, coll_name, file_id):
        """
        从gridFS删除文件
        :param coll_name:
        :param file_id:
        :return:
        """
        try:
            fs = GridFS(self.db, coll_name)
            fs.delete(ObjectId(file_id))
        except Exception:
            raise exc.DeleteException(
                '{}Delete file from "{}" failed! _id: {}, error: {}'.format(
                    self.log_prefix, coll_name, file_id, traceback.format_exc())
            )
        return True
