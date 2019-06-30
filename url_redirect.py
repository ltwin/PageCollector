"""
尝试获取跳转的url
"""
import aiohttp
import re

from loguru import logger
from urllib import parse

from common import get_host_from_url


async def redirect(url, page_content, headers):
    """
    解析跳转站点，包含meta标签实现的跳转、js脚本执行跳转，但并不能覆盖所有场景
    :param url: 跳转前的url
    :param page_content: 跳转前的页面内容
    :param headers: 请求头
    :return: response -> response object
    """
    if not (isinstance(page_content, str) and isinstance(url, str)):
        raise TypeError("Input param page_content and url should be string!")

    req_mata = await meta_redirect(url, page_content, headers)
    if req_mata:
        return req_mata

    req_loc = await location_replace_redirect(url, page_content, headers)
    if req_loc:
        return req_loc

    req_js = await java_script_redirect(url, page_content, headers)
    if req_js:
        return req_js

    req_js_in = await java_script_redirect_location_in_js(url, page_content, headers)
    if req_js_in:
        return req_js_in

    else:
        return ''


async def java_script_redirect(url, page_content, headers):
    """
    尝试获取js跳转后的页面
    :param url:
    :param page_content:
    :param headers:
    :return:
    """
    body_len_max = 100
    url_trail, resp = '', ''
    target_url = url
    body_re = re.compile('<body(.*?)</body>', re.IGNORECASE | re.S)
    #script_re = re.compile('<script>(.*)</script>', re.IGNORECASE | re.S)
    redirect_re_1 = re.compile('top.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    redirect_re_2 = re.compile('window.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    redirect_re_3 = re.compile('window.navigate\(\"(.*?)\"\)', re.IGNORECASE | re.S)
    redirect_re_4 = re.compile('self.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    #check if have a body less than 100chars, and a script with redirection in body
    match_body = body_re.search(page_content)
    parse_text = ''
    if match_body:
        parse_text = match_body.groups()[0].replace('\r\n', '').strip()
    else:
        parse_text = page_content

    if (match_body is not None and len(parse_text)
        <= body_len_max) or (match_body is None):
        match_redirect_1 = redirect_re_1.search(parse_text)
        match_redirect_2 = redirect_re_2.search(parse_text)
        match_redirect_3 = redirect_re_3.search(parse_text)
        match_redirect_4 = redirect_re_4.search(parse_text)
        if match_redirect_1:
            url_trail = match_redirect_1.groups()[0].strip()
        elif match_redirect_2:
            url_trail = match_redirect_2.groups()[0].strip()
        elif match_redirect_3:
            url_trail = match_redirect_3.groups()[0].strip()
        elif match_redirect_4:
            url_trail = match_redirect_4.groups()[0].strip()
        target_url = parse.urljoin(target_url, url_trail)
        if target_url != url:
            logger.info("Suspect java_script_redirect url"
                        " found:{}".format(target_url))

        try:
            if (get_host_from_url(target_url) !=
                    get_host_from_url(url) and headers is not None):
                headers['Host'] = get_host_from_url(target_url)
                headers['referer'] = url
            resp = await aiohttp.request('GET', target_url, headers=headers)
        except Exception as err:
            logger.info("Suspect js_redirect url access failed:"
                        " {}; errmsg: {}".format(target_url,str(err)))

    return resp


async def java_script_redirect_location_in_js(url, page_content, headers):
    """
    获取location跳转后的页面
    :param url:
    :param page_content:
    :param headers:
    :return:
    """
    body_len_max = 1000
    url_trail, resp = '', ''
    target_url = url
    script_re = re.compile('<script>(.*?)</script>', re.IGNORECASE | re.S)
    #script_re = re.compile('<script>(.*)</script>', re.IGNORECASE | re.S)
    redirect_re_1 = re.compile('location=\"(.*?)\"', re.IGNORECASE | re.S)
    #check if have a body less than 100chars, and a script with redirection in body
    match_script = script_re.search(page_content)
    parse_text = ''
    if match_script:
        parse_text = match_script.groups()[0].replace('\r\n', '').strip()
    else:
        parse_text = page_content

    if (match_script is not None and len(parse_text) <= body_len_max) or (match_script is None):
        match_redirect_1 = redirect_re_1.search(parse_text)
        if match_redirect_1:
            url_trail = match_redirect_1.groups()[0].strip()

        if url_trail == '':
            return ''
        target_url = parse.urljoin(target_url, url_trail)
        if target_url != url:
            logger.info("Suspect java_script_redirect url found:{}".format(target_url))

        try:
            if get_host_from_url(target_url) != get_host_from_url(url) and headers is not None:
                headers['Host'] = get_host_from_url(target_url)
                headers['referer'] = url
            resp = await aiohttp.request('GET', target_url, headers=headers)
        except Exception as e:
            logger.info("Suspect js_redirect url access failed:{};errmsg:{}".format(target_url,str(e)))
    return resp


async def meta_redirect(url, page_content, headers):
    """
    获取meta标签中的跳转页面
    :param url:
    :param page_content:
    :param headers:
    :return:
    """
    head_re = re.compile('<head(.*?)</head>', re.IGNORECASE | re.S)
    meta_redirect_re_1 = re.compile('<meta[^>]*?url=(.*?)[\"\']', re.IGNORECASE| re.S)
    #redirect_re = re.compile('url=(.*)[\'\"]', re.IGNORECASE| re.S)
    target_url = url
    resp = ""
    match_head = head_re.search(page_content)
    if match_head:
        match_meta_1 = meta_redirect_re_1.search(match_head.groups()[0])
        if match_meta_1:
            target_url = parse.urljoin(target_url, match_meta_1.groups()[0].strip())
            if get_host_from_url(target_url) != get_host_from_url(url) and headers is not None:
                headers['Host'] = get_host_from_url(target_url)
                headers['referer'] = url
            try:
                resp = await aiohttp.request('GET', target_url, headers=headers)
            except Exception as err:
                logger.warning('Get redirect page content '
                                'from tag meta failed, err: %s' % err)

    if url != target_url:
        logger.info("Meta redirect url found:{}".format(target_url))
    return resp


async def location_replace_redirect(url, page_content, headers):
    """
    获取location自动跳转的页面
    :param url:
    :param page_content:
    :param headers:
    :param timeout:
    :return:
    """
    url_trail ,resp = '', ''
    target_url = url
    head_re = re.compile('<head(.*?)</head>', re.IGNORECASE | re.S)
    head_onload_re = re.compile('window.onload(.*?)}', re.IGNORECASE | re.S)
    head_onload_redirect_re_1 = re.compile('top.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    head_onload_redirect_re_2 = re.compile('window.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    head_onload_redirect_re_3 = re.compile('window.navigate\(\"(.*?)\"\)', re.IGNORECASE | re.S)
    head_onload_redirect_re_4 = re.compile('self.location.href=\"(.*?)\"', re.IGNORECASE | re.S)
    match_head = head_re.search(page_content)
    if match_head:
        match_onload = head_onload_re.search(match_head.groups()[0])
        if match_onload:
            match_head_redirect_1 = head_onload_redirect_re_1.search(match_onload.groups()[0])
            match_head_redirect_2 = head_onload_redirect_re_2.search(match_onload.groups()[0])
            match_head_redirect_3 = head_onload_redirect_re_3.search(match_onload.groups()[0])
            match_head_redirect_4 = head_onload_redirect_re_4.search(match_onload.groups()[0])
            if match_head_redirect_1:
                url_trail = match_head_redirect_1.groups()[0].strip()
            elif match_head_redirect_2:
                url_trail = match_head_redirect_2.groups()[0].strip()
            elif match_head_redirect_3:
                url_trail = match_head_redirect_3.groups()[0].strip()
            elif match_head_redirect_4:
                url_trail = match_head_redirect_4.groups()[0].strip()
            target_url = parse.urljoin(target_url, url_trail)
            try:
                if get_host_from_url(target_url) != get_host_from_url(url) and 'Host' in headers.keys():
                    headers['Host'] = get_host_from_url(target_url)
                if get_host_from_url(target_url) != get_host_from_url(
                        url) and 'referer' in headers.keys():
                    headers['referer'] = url
                resp = await aiohttp.request('GET', target_url, headers=headers)
            except Exception as err:
                logger.warning("Location_replace redirect access failed:{}".format(str(err)))

    if url != target_url:
        logger.info("Location_replace redirect url found:{}".format(target_url))
    return resp
