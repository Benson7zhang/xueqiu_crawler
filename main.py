"""
雪球财经爬虫主程序

项目目标：
1. 通过浏览器开发者工具分析接口
2. 爬取股票榜单与详情数据
3. 默认保存到 MySQL 数据库，并同步输出 CSV，也可选只保存 CSV / SQLite
4. 展示重试、日志、异常隔离等稳定性设计
"""

import argparse
import os
import platform
import subprocess
import sys

from crawler import StockListCrawler, StockDetailCrawler
from crawler.base import parse_cookie_string
from storage import CSVStorage, MySQLStorage, SQLiteStorage
from utils.logger import setup_logger
import config


DEMO_STRATEGY = """
雪球财经爬虫运行流程

1. 网站分析
   - 打开雪球网页，使用浏览器开发者工具 Network 面板。
   - 筛选 Fetch/XHR 请求，定位股票榜单接口 list.json。
   - 再点击单只股票，定位详情接口 quote.json。

2. 请求还原
   - 复制接口 URL、Query 参数、User-Agent、Referer、Origin。
   - Cookie 可以从剪贴板读取，也可以用 Selenium 打开浏览器登录后读取。
   - 使用 requests.Session 复用会话，避免每次请求都像全新访客。

3. 请求稳定性处理
   - 设置正常浏览器请求头，说明服务器会检查访问来源和客户端特征。
   - 设置请求间隔，默认低频小规模抓取，避免高频访问。
   - 对超时、连接失败、HTTP 失败执行有限重试。
   - 如果遇到 403、429、验证码或非 JSON 响应，记录日志并停止。

4. 数据结构化
   - 榜单接口提取 symbol/name/current/percent 等列表字段。
   - 详情接口按 symbol 补充 open/high/low/market_capital/pe_ttm 等字段。
   - 保存到 MySQL 数据库，并同步输出 CSV 文件，展示原始 JSON 到结构化数据的映射。

5. 常用命令
   python3 main.py
   python3 main.py --boards gain --max-stocks 10
   python3 main.py --boards gain,loss --max-stocks 20
""".strip()


def build_parser():
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="雪球财经数据爬虫")
    parser.add_argument(
        '--explain-strategy',
        action='store_true',
        help='只输出运行流程，不发送网络请求',
    )
    parser.add_argument(
        '--max-stocks',
        type=int,
        default=config.MAX_STOCK_COUNT,
        help='最多抓取的股票数量，默认10只',
    )
    parser.add_argument(
        '--boards',
        default=','.join(config.DEFAULT_BOARDS),
        help='榜单类型，多个用逗号分隔：gain,loss,hot,amount',
    )
    parser.add_argument(
        '--storage',
        choices=['sqlite', 'csv', 'mysql'],
        default=config.STORAGE_TYPE,
        help='存储方式，默认mysql；mysql模式会同时输出CSV',
    )
    parser.add_argument(
        '--cookie-source',
        choices=['clipboard', 'selenium'],
        default=config.COOKIE_SOURCE,
        help='Cookie来源：clipboard读取剪贴板，selenium打开浏览器登录后读取',
    )
    return parser


def parse_boards(raw_boards):
    """解析榜单参数。"""
    boards = [item.strip() for item in (raw_boards or '').split(',') if item.strip()]
    return boards or ['gain']


def read_cookie_from_clipboard():
    """读取当前剪贴板内容。"""
    system_name = platform.system()
    commands = []
    if system_name == 'Darwin':
        commands = [['pbpaste']]
    elif system_name == 'Windows':
        commands = [['powershell', '-NoProfile', '-Command', 'Get-Clipboard -Raw']]
    else:
        commands = [
            ['wl-paste'],
            ['xclip', '-selection', 'clipboard', '-o'],
            ['xsel', '--clipboard', '--output'],
        ]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except Exception:
            continue

        text = result.stdout.strip()
        if text:
            return text

    return ''


def build_cookie_string(cookie_items):
    """把 Selenium 读取到的 Cookie 列表拼成请求头格式。"""
    pairs = []
    for item in cookie_items:
        name = item.get('name')
        value = item.get('value')
        if name and value is not None:
            pairs.append(f"{name}={value}")
    return '; '.join(pairs)


def is_login_cookie(cookie):
    """判断 Cookie 是否包含雪球登录态的关键字段。"""
    cookie_dict = parse_cookie_string(cookie)
    if not cookie_dict:
        return False
    has_token = 'xq_a_token' in cookie_dict or 'xq_id_token' in cookie_dict
    has_user = cookie_dict.get('xq_is_login') == '1' or 'u' in cookie_dict
    return has_token and has_user


def prompt_cookie_from_clipboard(input_fn=input, print_fn=print):
    """从剪贴板读取 Cookie。"""
    print_fn("\n请先复制雪球 Cookie。")
    print_fn("获取方式：登录雪球 -> F12 -> Network -> 任意请求 -> Request Headers -> Cookie")
    print_fn("复制完成后在 Cookie> 直接按回车，程序会读取剪贴板。")

    while True:
        input_fn("Cookie> ")
        cookie = read_cookie_from_clipboard()
        if is_login_cookie(cookie):#cookies格式判读
            config.XUEQIU_COOKIE = cookie
            print_fn("已从剪贴板读取 Cookie，开始运行。")
            return cookie

        print_fn("剪贴板里没有有效登录 Cookie，请重新复制后再按回车。")


def prompt_cookie_from_selenium(input_fn=input, print_fn=print):
    """用 Selenium 打开浏览器，登录后读取 Cookie。"""
    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException, WebDriverException
    except ImportError as e:
        raise RuntimeError(
            "未安装 selenium，请先运行：pip install -r requirements.txt"
        ) from e

    print_fn("\n正在启动 Selenium 控制的 Chrome 浏览器，请稍等。")
    print_fn("首次运行时 Selenium 会自动准备 ChromeDriver，可能需要等待几十秒。")
    print_fn("注意：必须在 Selenium 打开的浏览器里登录，手动打开的普通 Chrome 读不到。")

    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    if config.CHROME_BINARY_PATH and os.path.exists(config.CHROME_BINARY_PATH):
        options.binary_location = config.CHROME_BINARY_PATH

    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as e:
        raise RuntimeError(
            "Selenium 启动 Chrome 失败。请确认已安装 Google Chrome，"
            "并使用项目虚拟环境运行：python3 main.py --cookie-source selenium"
        ) from e

    try:
        driver.set_page_load_timeout(config.SELENIUM_PAGE_LOAD_TIMEOUT)
        print_fn("浏览器已启动，正在打开雪球首页。")

        try:
            driver.get(config.XUEQIU_BASE_URL)
        except TimeoutException:
            print_fn("雪球首页加载较慢，请在打开的浏览器地址栏手动访问 https://xueqiu.com")

        print_fn("请在这个浏览器中登录雪球。")
        input_fn("登录完成后回到这里，按回车继续> ")

        try:
            driver.get(config.XUEQIU_BASE_URL)
        except TimeoutException:
            print_fn("页面刷新超时，继续尝试读取当前浏览器 Cookie。")

        cookie = build_cookie_string(driver.get_cookies())
        if not is_login_cookie(cookie):
            raise RuntimeError("没有读取到有效 Cookie，请确认浏览器里已经登录雪球。")

        config.XUEQIU_COOKIE = cookie
        print_fn("已通过 Selenium 读取 Cookie，开始运行。")
        return cookie
    finally:
        driver.quit()


def prompt_cookie(cookie_source='clipboard', input_fn=input, print_fn=print):
    """按指定来源获取 Cookie。"""
    if cookie_source == 'selenium':
        return prompt_cookie_from_selenium(input_fn=input_fn, print_fn=print_fn)
    return prompt_cookie_from_clipboard(input_fn=input_fn, print_fn=print_fn)


class XueqiuCrawler:
    """
    雪球财经爬虫主类
    协调各个爬虫模块和存储模块的工作
    """

    def __init__(self, *, max_stocks=None, boards=None, storage_type=None):
        """初始化爬虫。"""
        self.max_stocks = max_stocks or config.MAX_STOCK_COUNT
        self.boards = boards or config.DEFAULT_BOARDS
        self.storage_type = storage_type or config.STORAGE_TYPE

        self.logger = setup_logger('XueqiuCrawler')
        self.logger.info("=" * 60)
        self.logger.info("雪球财经数据爬虫启动")
        self.logger.info("=" * 60)

        # 初始化爬虫模块
        self.stock_list_crawler = StockListCrawler()
        self.stock_detail_crawler = StockDetailCrawler()
        self.csv_storage = None

        # 初始化存储模块
        if self.storage_type == 'sqlite':
            self.storage = SQLiteStorage()
            self.logger.info("使用SQLite数据库存储模式")
        elif self.storage_type == 'csv':
            self.storage = CSVStorage()
            self.logger.info("使用CSV存储模式")
        elif self.storage_type == 'mysql':
            self.storage = MySQLStorage()
            self.csv_storage = CSVStorage()
            self.logger.info("使用MySQL存储模式，并同步输出CSV")
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")

    def run(self):
        """
        运行爬虫主流程。

        流程：
        1. 获取股票榜单
        2. 获取每只股票的详细信息
        3. 保存所有数据
        """
        stock_details = []

        try:
            # ==================== 步骤1: 获取股票列表 ====================
            self.logger.info("\n" + "=" * 60)
            self.logger.info("步骤1: 获取股票榜单列表")
            self.logger.info("=" * 60)

            stock_list = self.stock_list_crawler.get_stocks_by_boards(
                boards=self.boards,
                total_count=self.max_stocks,
            )

            if not stock_list:
                self.logger.error("未获取到股票列表，程序终止")
                return False

            self.logger.info(f"成功获取 {len(stock_list)} 只股票")
            self._save_stock_list(stock_list)

            # ==================== 步骤2: 获取股票详情 ====================
            self.logger.info("\n" + "=" * 60)
            self.logger.info("步骤2: 获取股票详细信息")
            self.logger.info("=" * 60)

            symbols = [stock['symbol'] for stock in stock_list]
            stock_details = self.stock_detail_crawler.get_batch_details(symbols)

            if stock_details:
                self.logger.info(f"成功获取 {len(stock_details)} 只股票详情")
                self._save_stock_details(stock_details)
            else:
                self.logger.warning("未获取到股票详情")

            # ==================== 完成 ====================
            self.logger.info("\n" + "=" * 60)
            self.logger.info("爬虫任务完成！")
            self.logger.info("=" * 60)
            self.logger.info(f"股票列表: {len(stock_list)} 条")
            self.logger.info(f"股票详情: {len(stock_details)} 条")
            self.logger.info("=" * 60)
            return True

        except KeyboardInterrupt:
            self.logger.warning("\n用户中断程序")
            return False
        except Exception as e:
            self.logger.error(f"爬虫运行出错: {e}", exc_info=True)
            raise
        finally:
            self.cleanup()

    def _save_stock_list(self, stock_list):
        """保存股票榜单；MySQL模式下额外输出CSV。"""
        self.storage.save_stock_list(stock_list)
        if self.csv_storage:
            try:
                self.csv_storage.save_stock_list(stock_list)
            except Exception as e:
                self.logger.warning(f"CSV股票榜单保存失败，MySQL数据已保存: {e}")

    def _save_stock_details(self, stock_details):
        """保存股票详情；MySQL模式下额外输出CSV。"""
        self.storage.save_stock_details(stock_details)
        if self.csv_storage:
            try:
                self.csv_storage.save_stock_details(stock_details)
            except Exception as e:
                self.logger.warning(f"CSV股票详情保存失败，MySQL数据已保存: {e}")

    def cleanup(self):
        """清理资源。"""
        self.logger.info("清理资源...")

        for resource_name in ('stock_list_crawler', 'stock_detail_crawler', 'storage'):
            resource = getattr(self, resource_name, None)
            if not resource or not hasattr(resource, 'close'):
                continue
            try:
                resource.close()
            except Exception as e:
                self.logger.warning(f"关闭资源失败: {resource_name}, {e}")


        self.logger.info("资源清理完成")


def main(argv=None):
    """主函数入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.explain_strategy:
        print(DEMO_STRATEGY)
        return 0

    try:
        prompt_cookie(args.cookie_source)
        crawler = XueqiuCrawler(
            max_stocks=args.max_stocks,
            boards=parse_boards(args.boards),
            storage_type=args.storage,
        )
        return 0 if crawler.run() else 1
    except Exception as e:
        print(f"程序异常退出: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
