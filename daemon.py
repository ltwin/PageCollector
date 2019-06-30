"""
守护进程基类
"""

import os
import signal
import sys
import time


class Daemon(object):
    """一个普通的守护类。
    Usage: 继承该守护类并重写_run方法。
    """

    def __init__(self, pidfile, workdir, daemon=True, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        self.daemon = daemon
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._pidfile = pidfile
        self._workdir = workdir

    def _daemonize(self):
        """按UNIX的两次fork魔法把进程守护化。

        参考Steven的 "Advanced Programming in the UNIX Environment"。
        """

        # 第一次fork，脱离父进程，使程序得以后台运行
        try:
            pid = os.fork()

            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('Fork #1 failed: %d (%s)\n'
                             % (err.errno, err.strerror))
            sys.exit(1)
        os.setsid()  # 脱离终端
        os.chdir(self._workdir)
        os.umask(0o22)  # 重新设置文件创建权限

        # 第二次fork，禁止进程重新打开控制终端
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('Fork #2 failed: %d (%s)\n'
                             % (err.errno, err.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self._stdin, 'r')
        so = open(self._stdout, 'a+')
        se = open(self._stderr, 'a+')
        # 重定向标准输入/输出/错误
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # 创建pid文件
        pid = str(os.getpid())
        pid_dir = os.path.dirname(self._pidfile)
        if not os.path.isdir(pid_dir):
            os.mkdir(pid_dir)
        f = open(self._pidfile, 'w+')
        f.write('%s\n' % pid)
        f.close()

    def _delpid(self):
        os.remove(self._pidfile)

    def start(self):
        """启动守护进程。

        程序运行后进程立即守护化。
        """
        # Check for a pidfile to see if the app already runs
        try:
            pidfile = open(self._pidfile, 'r')
            pid = int(pidfile.read().strip())
            pidfile.close()
        except IOError:
            pid = None

        if pid:
            message = 'The pidfile %s already exist. Daemon already running?\n'
            sys.stderr.write(message % self._pidfile)
            sys.exit(1)

        # Start the app
        if self.daemon:
            self._daemonize()
        self._run()

    def stop(self):
        """结束守护进程。

        根据守护化进程的pid文件，结束进程。
        """
        try:
            pf = open(self._pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'The pidfile %s does not exist. Daemon not running?\n'
            sys.stderr.write(message % self._pidfile)
            return

            # 尝试给进程传递SIGTERM信号。
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.isfile(self._pidfile):
                    os.remove(self._pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """重启守护进程。

        重新启动是stop-start的过程。
        """
        self.stop()
        self.start()

    def _run(self):
        """继承守护类的类实现该方法。

        接口，被子类实现，该方法在调用start或restart守护进程化后被调用。
        """
        pass
