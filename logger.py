"""
Author: lt
Date: 2020-01-08
Desc: 自定义日志
"""
import glob
import logging
import os
import re
import string
import sys

from cloghandler import ConcurrentRotatingFileHandler
from datetime import date
from datetime import datetime
from logging import Handler
from loguru import logger

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} |" \
             " {level: <8} | {name}:" \
             "{function}:{line} - " \
             "{message}"
DEFAULT_MAX_BYTES = 1024 * 1024 * 200  # 200MB
ROTATE_DAYS = 1
RETENTION_DAYS = 30


class ConcurrentTimeRotatingFileHandler(ConcurrentRotatingFileHandler):

    def __init__(self, filename, mode='a',
                 maxBytes=0, backupCount=0,
                 encoding=None, debug=True,
                 delay=0, rotating_days=ROTATE_DAYS,
                 retention_days=RETENTION_DAYS):
        self.rotating_days = rotating_days
        self.retention_days = retention_days
        self.origin_name = filename
        filename = self.format_path(filename)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        super(ConcurrentTimeRotatingFileHandler, self).__init__(
            filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount,
            encoding=encoding, debug=debug, delay=delay)

    def _open_lockfile(self):
        if self.origin_name.endswith(".log"):
            lock_file = self.origin_name[:-4]
        else:
            lock_file = self.origin_name
        lock_file += ".lock"
        self.stream_lock = open(lock_file,"w")

    def format_path(self, filename):
        if not self.rotating_days:
            return os.path.abspath(filename)
        today_str = str(date.today()).replace('-', '')
        root, ext = os.path.splitext(filename)
        filename = ''.join([root, '_', today_str, ext])
        return os.path.abspath(filename)

    def make_glob_pattern(self):
        tokens = string.Formatter().parse(self.baseFilename)
        parts = (glob.escape(text) + "*" * (name is not None)
                 for text, name, *_ in tokens)
        root, ext = os.path.splitext("".join(parts))
        if ext:
            pattern = root + "*.%s*" % ext
        else:
            pattern = root + "*"
        return pattern

    def retention_func(self):
        """按时间删除一定时间之前的日志"""
        patterns = self.make_glob_pattern()
        logs = glob.glob(patterns)
        for log in logs:
            mtime = os.stat(log).st_mtime
            mtime_date = datetime.fromtimestamp(mtime)
            if (datetime.now() - mtime_date).days > self.retention_days:
                try:
                    os.remove(log)
                except (OSError, FileNotFoundError) as err:
                    logger.error('Remove file "%s" failed! '
                                 'The error: %s' % (log, err))

    def time_rotate(self):
        match_results = re.findall('\d{8}', self.baseFilename)
        if not match_results:
            logger.warning('Cannot match time string from filename!')
            return
        old_time = match_results[0]
        old_time = datetime.strptime(old_time, '%Y%m%d')
        if (datetime.now() - old_time).days <= self.rotating_days:
            # 没有到达切换日期
            return
        new_name = self.format_path(self.origin_name)
        if self.baseFilename != new_name:
            self._close()
            self.baseFilename = new_name
            self.stream = self._open()
            # 判定删除一定时间之前的日志
            self.retention_func()

    def _shouldRollover(self):
        # Windows上使用ctime可以获取到创建时间，因为NTFS文件系统支持，
        # 但Linux上所使用的ext2文件系统则没有创建时间的概念，
        # 除非使用最新的ext4文件系统，这样一来，
        # 所谓的ctime也会随着文件的元数据的变化而变化（操作权限、所在目录、所有者等）
        # 所以不能使用ctime作为日志按时间切换的依据
        if self.rotating_days > 0:
            self.time_rotate()
        if self.maxBytes > 0:
            self.stream.seek(0, 2)
            if self.stream.tell() >= self.maxBytes:
                return True
            else:
                self._degrade(
                    False, "Rotation done or not needed at this time")
        return False

    def close(self):
        try:
            self._close()
            if not self.stream_lock.closed:
                self.stream_lock.close()
        except AttributeError:
            pass
        finally:
            self.stream_lock = None
            Handler.close(self)


def init_logger(path, level='INFO',
                max_bytes=DEFAULT_MAX_BYTES,
                backup_count=5):
    # 使用多进程安全的handler作为loguru的sink
    sink = ConcurrentTimeRotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup_count)
    log_config = {
        "handlers": [
            {"sink": sys.stdout, "format": LOG_FORMAT,
             "level": level, "colorize": False},
            # enqueue置为False吧，它因为启动了一个内置线程来使用queue写入日志保证多进程安全，
            # 这样似乎会与gunicorn等等webserver产生冲突，因此先置为False，原因具体再查  --by lt
            {
                "sink": sink, "format": LOG_FORMAT,
                "level": level, "enqueue": False, "colorize": False
            },
        ]
    }
    logger.configure(**log_config)
