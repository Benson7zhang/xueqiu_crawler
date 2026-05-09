"""
配置文件
包含爬虫运行所需的各项配置参数。

项目不要把 Cookie 写死在源码中。
运行 `python3 main.py` 后，按提示读取 Cookie。
"""

import os


# ==================== 爬虫基础配置 ====================
XUEQIU_COOKIE = ''#cookies临时保存在这
# clipboard：从剪贴板读取；selenium：打开浏览器登录后读取
COOKIE_SOURCE = os.getenv('COOKIE_SOURCE', 'clipboard')
SELENIUM_PAGE_LOAD_TIMEOUT = int(os.getenv('SELENIUM_PAGE_LOAD_TIMEOUT', '30'))
CHROME_BINARY_PATH = os.getenv(
    'CHROME_BINARY_PATH',
    ''
)


# 请求头配置
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://xueqiu.com/',
    'Origin': 'https://xueqiu.com',
}

# 请求间隔配置（秒）
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.5'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))

# 重试配置
MAX_RETRY_TIMES = int(os.getenv('MAX_RETRY_TIMES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))

# ==================== 雪球网站配置 ====================
XUEQIU_BASE_URL = 'https://xueqiu.com'
HOT_STOCK_URL = 'https://stock.xueqiu.com/v5/stock/screener/quote/list.json'
STOCK_DETAIL_URL = 'https://stock.xueqiu.com/v5/stock/quote.json'

# ==================== 数据存储配置 ====================
# 默认保存到MySQL，并同步输出CSV。
# 如需只保存CSV可运行：python3 main.py --storage csv
# 如需SQLite可运行：python3 main.py --storage sqlite
STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'mysql')
CSV_OUTPUT_DIR = os.getenv('CSV_OUTPUT_DIR', './data')
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', './data/xueqiu.db')

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'xueqiu_data'),
    'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4'),
}

# ==================== 爬取范围配置 ====================
# 默认只抓少量数据，保证运行稳定、等待时间可控。
MAX_STOCK_COUNT = int(os.getenv('MAX_STOCK_COUNT', '10'))
DEFAULT_BOARDS = [
    item.strip()
    for item in os.getenv('XUEQIU_BOARDS', 'gain').split(',')
    if item.strip()
]

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', './logs/crawler.log')
LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', '1') != '0'
