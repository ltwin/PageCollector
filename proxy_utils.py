"""
IP代理池使用前置
"""

import aiohttp
import json

from aiohttp import ClientTimeout
from loguru import logger

import common as cm
import config as conf

from url_redirect import redirect


async def get_proxy():
    """获取一个代理IP"""
    async with aiohttp.request('GET', conf.GET_ONE_PROXY_IP_URL) as resp:
        return await resp.read()


async def get_all_proxies():
    """获取所有代理IP"""
    async with aiohttp.request('GET', conf.GET_ALL_PROXY_IPS_URL) as resp:
        resp_data = await resp.read()
        all_proxies = json.loads(resp_data)
        return all_proxies


async def delete_proxy(proxy):
    """从代理池中删除代理IP"""
    async with aiohttp.request('GET', conf.DELETE_PROXY_IP_URL,
                               params={'proxy': proxy}) as resp:
        return resp.read()


async def aio_request(method, url, params=None, json=None,
                      headers=None, proxy_ip=None,
                      parse_redirect_url=True, timeout=5 * 60):
    """
    异步请求并获取返回结果
    :param method: HTTP标准方法
    :param url: 请求url
    :param params: 请求参数
    :param json: 请求json数据
    :param json: 请求json数据
    :param headers: 请求头
    :param proxy_ip: 代理ip
    :param parse_redirect_url: 是否解析重定向的url
    :param timeout: 请求超时时间(单位：秒)
    :return:
    """
    timeout_obj = ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url, timeout=timeout_obj, params=params, json=json,
                               headers=headers, proxy=proxy_ip, verify_ssl=False) as resp:
            content = await resp.read()
            page_text = cm.guess_and_decode(content)
            if parse_redirect_url:
                redirect_resp = await redirect(url, page_text, headers=headers)
                if redirect_resp:
                    content = await redirect_resp.read()
                    page_text = cm.guess_and_decode(content)
            return content, page_text


async def request_with_proxy(method, url, params=None, json=None,
                             headers=None, parse_redirect_url=True,
                             timeout=5 * 60):
    """
    尝试使用代理池请求目标
    :param method: 标准http请求方法
    :param url: 请求url
    :param params: 请求参数
    :param json: 请求json数据
    :param headers: 请求头
    :param parse_redirect_url: 是否解析重定向url
    :param timeout: 请求超时时间
    :return:
    """
    all_proxy_ips = await get_all_proxies()
    loop_count = 0
    for proxy_ip in all_proxy_ips:
        if loop_count > conf.PROXY_TRIED_TIMES:
            return '', ''
        for i in range(conf.RETRY_TIMES):
            try:
                return await aio_request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    proxy_ip=proxy_ip,
                    parse_redirect_url=parse_redirect_url,
                    timeout=timeout
                )
            except Exception as err:
                logger.warning('Download page content failed, now retry'
                               'url: {}, proxy: {}, error: {}'.format(url, proxy_ip, err))
                continue
        loop_count += 1