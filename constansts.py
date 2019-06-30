"""
常量
"""

# 常见user-agent
USER_AGENT = [
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7',
    'Mozilla/5.0+(compatible;+Baiduspider/2.0;++http://www.baidu.com/search/spider.html)',
    'Mozilla/5.0+(compatible;+MSIE+9.0;+Windows+NT+6.1;+Trident/5.0);+360Spider',
    'Sogou+web+spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)',
]

# 不是页面链接的常见的后缀
IGNORED_EXTENSIONS = [
    # 图像
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg',

    # 音频
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # 视频
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # 办公套件
    'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg',
    'odp',

    # 其他
    'css', 'pdf', 'exe', 'bin', 'rss', 'zip', 'rar', 'apk'
]

# 常见的两段式顶级域名，在解析二级域名时需要忽略掉
IGNORED_SLD_LIST = [".ac.cn", ".com.cn", ".org.cn", ".net.cn", ".gov.cn", ".mil.cn", ".edu.cn",
                        ".ah.cn", ".bj.cn", ".cq.cn", ".fj.cn", ".gd.cn",
                        ".gs.cn", ".gz.cn", ".gx.cn", ".ha.cn", ".hb.cn",
                        ".he.cn", ".hi.cn", ".hl.cn", ".hn.cn", ".jl.cn", ".js.cn",
                        ".jx.cn", ".ln.cn", ".nm.cn", ".nx.cn", ".qh.cn",
                        ".sc.cn", ".sd.cn", ".sh.cn", ".sn.cn", ".sx.cn",
                        ".tj.cn", ".xj.cn", ".xz.cn", ".yn.cn", ".zj.cn",
                        ".hk.cn", ".mo.cn", ".tw.cn"]

# 常见的页面扩展名
PAGE_EXTENSION_LIST = ['html', 'htm', 'php', '.asp', 'aspx', 'jsp', 'shtml', 'nsp', 'cgi']
