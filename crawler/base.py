"""
基础爬虫类
提供通用的HTTP请求、异常处理等功能
封装公共请求逻辑
"""

import requests
import time
import re
from abc import ABC, abstractmethod
from utils.logger import setup_logger
from utils.retry import retry_on_failure
import config


COOKIE_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$')


def parse_cookie_string(cookie):
    text = (cookie or '').strip()
    if not text:
        return {}

    result = {}
    for item in text.split(';'):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            return {} #必须有等号否则返回空字典表示解析失败
        key, value = item.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key or not COOKIE_KEY_PATTERN.match(key):#检查键非空、符合正则表达式
            return {}
        result[key] = value
    return result


class BaseCrawler(ABC):
    """
    爬虫基类
    所有具体爬虫都应继承此类并实现parse方法
    """

    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()#复用请求状态
        self.session.headers.update(config.HEADERS)
        self.logger = setup_logger(self.__class__.__name__)
        # 设置Cookie
        self._setup_cookies()
        self.logger.info(f"{self.__class__.__name__} 初始化完成")

    def _setup_cookies(self):
        """
        设置Cookie
        优先使用配置文件中的Cookie，如果没有则访问首页获取
        """
        cookie_dict = parse_cookie_string(config.XUEQIU_COOKIE)
        if cookie_dict:
            # 使用配置的Cookie
            self.logger.debug("使用配置的Cookie")

            # 设置Cookie到session
            for key, value in cookie_dict.items():
                self.session.cookies.set(key, value, domain='.xueqiu.com')

            self.logger.info("已加载登录Cookie")
        else:
            if config.XUEQIU_COOKIE:
                self.logger.warning("Cookie格式无效，已忽略。请粘贴纯Cookie字符串，不要粘贴curl命令。")
            # 访问首页获取基础Cookie
            self.logger.debug("未配置Cookie，访问首页获取...")
            try:
                response = self.session.get(
                    'https://xueqiu.com',
                    timeout=config.REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    self.logger.debug("基础Cookie获取成功")
                else:
                    self.logger.warning(f"Cookie获取异常，状态码: {response.status_code}")
            except Exception as e:
                self.logger.warning(f"获取Cookie失败: {e}")

    @retry_on_failure(exceptions=(requests.RequestException, ConnectionError))
#网络请求可能临时失败，比如超时、连接错误
    def fetch(self, url, method='GET', params=None, data=None, **kwargs):
        """
        发送HTTP请求并返回原始 response
        Args:
            url: 请求URL
            method: 请求方法（GET/POST）
            params: URL参数
            data: POST数据
            **kwargs: 其他requests参数
        Returns:
            requests.Response: 响应对象
        Raises:
            requests.RequestException: 请求失败时抛出
        """
        try:
            self.logger.debug(f"请求 {method} {url}")

            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                timeout=config.REQUEST_TIMEOUT,
                **kwargs
            )

            # 检查响应状态
            response.raise_for_status()

            self.logger.debug(f"请求成功: {url} (状态码: {response.status_code})")

            # 请求间隔延迟
            time.sleep(config.REQUEST_DELAY)
            return response

        except requests.HTTPError as e:
            self.logger.error(f"HTTP错误: {e} (URL: {url})")
            raise
        except requests.ConnectionError as e:
            self.logger.error(f"连接错误: {e} (URL: {url})")
            raise
        except requests.Timeout as e:
            self.logger.error(f"请求超时: {e} (URL: {url})")
            raise
        except Exception as e:
            self.logger.error(f"未知错误: {e} (URL: {url})")
            raise

    def fetch_json(self, url, method='GET', params=None, data=None, **kwargs):
        """
        先调用 fetch()，再执行 response.json()，把返回结果转成 Python 字典
        Args:
            url: 请求URL
            method: 请求方法
            params: URL参数
            data: POST数据
            **kwargs: 其他requests参数
        Returns:
            dict: 解析后的JSON数据
        """
        response = self.fetch(url, method, params, data, **kwargs)
        try:
            return response.json()
        except ValueError as e:
            content_type = response.headers.get('Content-Type', '')
            self.logger.error(
                f"JSON解析失败: {e}; 状态码={response.status_code}; "
                f"Content-Type={content_type}"
            )
            raise

    @abstractmethod
    def parse(self, *args, **kwargs):
        """
        解析数据的抽象方法
        子类必须实现此方法
        """
        pass

    def run(self):
        """
        运行爬虫的主方法
        子类可以重写此方法实现自定义逻辑
        """
        self.logger.info(f"{self.__class__.__name__} 开始运行")
        try:
            result = self.parse()
            self.logger.info(f"{self.__class__.__name__} 运行完成")
            return result
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} 运行失败: {e}")
            raise

    def close(self):
        """关闭会话"""
        self.session.close()
        self.logger.info(f"{self.__class__.__name__} 会话已关闭")
