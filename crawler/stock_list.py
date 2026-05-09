"""
股票列表爬虫
获取雪球热门股票列表数据
"""

from .base import BaseCrawler
from datetime import datetime
import config


BOARD_CONFIG = {
    'hot': {'order': 'desc', 'orderby': 'percent', 'label': '热门榜'},
    'gain': {'order': 'desc', 'orderby': 'percent', 'label': '涨幅榜'},
    'loss': {'order': 'asc', 'orderby': 'percent', 'label': '跌幅榜'},
    'amount': {'order': 'desc', 'orderby': 'amount', 'label': '成交额榜'},
}


class StockListCrawler(BaseCrawler):
    """
    股票列表爬虫类
    用于获取雪球网站的热门股票列表
    """

    def __init__(self):
        """初始化股票列表爬虫"""
        super().__init__()
        self.stock_list_url = config.HOT_STOCK_URL

    def parse(self, page=1, size=None, board='gain'):#默认是gain
        """
        解析股票列表数据

        Args:
            page: 页码，默认第1页
            size: 每页数量，默认使用配置中的MAX_STOCK_COUNT
            board: 榜单类型，gain=涨幅榜，loss=跌幅榜，amount=成交额榜

        Returns:
            list: 股票列表，每个元素为包含股票信息的字典
                [{
                    'symbol': 股票代码,
                    'name': 股票名称,
                    'current': 当前价格,
                    'percent': 涨跌幅,
                    'change': 涨跌额,
                    'volume': 成交量,
                    'amount': 成交额,
                    'turnover_rate': 换手率,
                    'market_capital': 总市值,
                    'pe_ttm': 市盈率TTM
                }, ...]
        """
        if size is None:
            size = config.MAX_STOCK_COUNT
        if board not in BOARD_CONFIG:
            raise ValueError(f"不支持的榜单类型: {board}")

        board_config = BOARD_CONFIG[board]

        self.logger.info(
            f"开始获取股票列表 (榜单: {board_config['label']}, 页码: {page}, 数量: {size})"
        )

        # 构建请求参数
        params = {
            'page': page,
            'size': size,
            'order': board_config['order'],
            'orderby': board_config['orderby'],
            'order_by': board_config['orderby'],
            'market': 'CN',
            'type': 'sh_sz'
        }

        try:
            # 发送请求获取JSON数据
            data = self.fetch_json(self.stock_list_url, params=params)

            # 检查响应数据结构
            if 'data' not in data or 'list' not in data['data']:
                self.logger.error(f"响应数据格式异常: {data}")
                return []

            stock_list = data['data']['list']
            self.logger.info(f"成功获取 {len(stock_list)} 只股票信息")

            # 解析并格式化股票数据
            result = []
            for stock in stock_list:
                try:
                    stock_info = {
                        'symbol': stock.get('symbol', ''),
                        'name': stock.get('name', ''),
                        'board': board_config['label'],
                        'current': stock.get('current', 0),
                        'percent': stock.get('percent', 0),
                        'change': stock.get('change', 0),
                        'volume': stock.get('volume', 0),
                        'amount': stock.get('amount', 0),
                        'turnover_rate': stock.get('turnover_rate', 0),
                        'market_capital': stock.get('market_capital', 0),
                        'pe_ttm': stock.get('pe_ttm', 0),
                        'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    result.append(stock_info)
                    self.logger.debug(f"解析股票: {stock_info['symbol']} - {stock_info['name']}")
                except Exception as e:
                    self.logger.warning(f"解析股票数据失败: {e}, 数据: {stock}")
                    continue

            return result

        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            raise

    def get_hot_stocks(self, count=None, board='gain'):
        """
        获取热门股票（按涨跌幅排序）
        Args:
            count: 获取数量，默认使用配置中的MAX_STOCK_COUNT
            board: 榜单类型

        Returns:
            list: 热门股票列表
        """
        if count is None:
            count = config.MAX_STOCK_COUNT

        return self.parse(page=1, size=count, board=board)

    def get_stocks_by_boards(self, boards=None, total_count=None):
        """
        按多个榜单抓取股票列表，并按股票代码去重。
        Args:
            boards: 榜单列表，如 ['gain', 'loss']
            total_count: 总抓取数量

        Returns:
            list: 去重后的股票列表
        """
        boards = boards or config.DEFAULT_BOARDS
        total_count = total_count or config.MAX_STOCK_COUNT
        result = []
        seen_symbols = set()
        remaining = total_count

        for index, board in enumerate(boards):
            if remaining <= 0:
                break
            boards_left = len(boards) - index
            quota = (remaining + boards_left - 1) // boards_left
            rows = self.parse(page=1, size=quota, board=board)#动态传入版单等数据

            for row in rows:
                symbol = row.get('symbol')
                if not symbol or symbol in seen_symbols:
                    continue
                seen_symbols.add(symbol)
                result.append(row)
                if len(result) >= total_count:
                    break
            remaining = total_count - len(result)

        self.logger.info(f"多榜单抓取完成，去重后共 {len(result)} 只股票")
        return result
