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
DEFAULT_REFERER = 'http://www.baidu.com/'

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
PAGE_EXTENSION_LIST = ['html', 'htm', 'php', 'asp', 'aspx', 'jsp', 'shtml', 'nsp', 'cgi']

# 页面中包含如下语句则舍弃
USELESS_PAGE_FEATURE = [
    '网站维护中',
    '管理员已屏蔽了此状态的详细信息',
    '404 Not Found',
    '403 Forbidden',
    '最近有可疑的攻击行为，请稍后重试',
    'Service Temporarily Unavailable',
    '请先登录身份认证系统！',
    '内容读取中',
    'Fatal error',
    '您的请求过于频繁',
    'Discuz! Database Error',
    'Can not connect to MySQL server',
    'exception.GenericJDBCException',
    'org.hibernate.TransactionException',
    '序列号验证错误，可能原因是你访问的域名与序列号不对应',
    '恭喜，站点创建成功！',
    '过于频繁的暴力刷新/访问网站页面',
    'freemarker.core.InvalidReferenceException',
    'java.lang.ClassCastException',
    '您访问的页面发生错误!',
    '此频道已经被管理员禁用！',
    '请稍后再访问此站点。如果您仍然遇到问题，请与网站的管理员联系。',
    '管理员已屏蔽了此状态的详细信息',
    '如果您服务器未配置任何防火墙，请与您的机房联系，将云防护的IP段添加到机房防火墙白名单中',
    'An error occurred during processing',
    'langouster IIS FireWall提醒您：您在注入本网站？特征字符',
    '抱歉！源站出现问题，暂时无法访问！',
    'This website is temporarily closed. Please try again later',
    '系统发生错误',
    '页面载入中',
    '访问本页面您的浏览器需要支持',
    '正在为您跳转到访问页面',
    '网站配置数据丢失系统无法正常运行',
    '首页跳转',
    '如果您的页面没有自动跳转请点击这里',
    '页面出错',
    '访问出错',
    'MYSQL.Connect.Error!',
    '您要查看的页面可能已经删除更名或暂时不可用',
    '系统中心内部服务器错误',
    '你的已被锁定请稍后再访问网站或联系管理员解锁',
    '网站不能正常访问',
    '点击链接后将跳转到访问页面',
    '用户登录失败',
    '服务器安全狗防护验证页面',
    '重置密码',
    '数据库连接出错',
    '错误分析提示',
    'Note: KesionCMS template engine to load the template does not exist.',
    '网站防火墙',
    'loading...',
    '具体错误信息',
    '错误系统异常您的提交带有不合法参数谢谢合作',
    '请开启并刷新该页',
    '你的已被锁定请稍后再访问网站或联系管理员解锁',
    '读取模板文件出错',
    '如果您的页面没有自动跳转请点击这里',
    'BadRequest(InvalidHostname)',
    '正在跳转',
    '页面请求失败',
    '服务器忙请稍后访问',
    '浏览器不支持请手动刷新页面',
    '正在为您跳转到访问页面如果您的浏览器没有自动跳转请检查以下'
    '设置请确保浏览器没有禁止发送请确保浏览器可以正常执行脚本若'
    '使用浏览器请使用及以上版本确保本地时间的准确性请观察这个时'
    '间若时间一直未变化则是由于验证页面被缓存可能是与设置不兼容',
]
