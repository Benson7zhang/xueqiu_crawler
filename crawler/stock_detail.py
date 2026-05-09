"""
股票详情爬虫
获取单只股票的详细信息
"""

from .base import BaseCrawler
import config


class StockDetailCrawler(BaseCrawler):
    """
    股票详情爬虫类
    用于获取单只股票的详细信息
    """

    def __init__(self):
        """初始化股票详情爬虫"""
        super().__init__()
        self.detail_url = config.STOCK_DETAIL_URL

    def parse(self, symbol):
        """
        解析股票详情数据

        Args:
            symbol: 股票代码，如 'SH600000' 或 'SZ000001'

        Returns:
            dict: 股票详细信息字典
                {
                    'symbol': 股票代码,
                    'name': 股票名称,
                    'current': 当前价格,
                    'percent': 涨跌幅,
                    'change': 涨跌额,
                    'open': 开盘价,
                    'high': 最高价,
                    'low': 最低价,
                    'close': 收盘价,
                    'last_close': 昨收价,
                    'volume': 成交量,
                    'amount': 成交额,
                    'turnover_rate': 换手率,
                    'market_capital': 总市值,
                    'float_market_capital': 流通市值,
                    'pe_ttm': 市盈率TTM,
                    'pe_lyr': 市盈率LYR,
                    'pb': 市净率,
                    'dividend_yield': 股息率,
                    'total_shares': 总股本,
                    'float_shares': 流通股本
                }
        """
        self.logger.info(f"开始获取股票详情: {symbol}")

        # 构建请求参数
        params = {
            'symbol': symbol,
            'extend': 'detail'
        }

        try:
            # 发送请求获取JSON数据
            data = self.fetch_json(self.detail_url, params=params)

            # 检查响应数据结构
            if 'data' not in data or 'quote' not in data['data']:
                self.logger.error(f"响应数据格式异常: {data}")
                return None

            quote = data['data']['quote']
            self.logger.info(f"成功获取股票详情: {quote.get('name', symbol)}")

            # 解析并格式化股票详情数据
            stock_detail = {
                'symbol': quote.get('symbol', ''),
                'name': quote.get('name', ''),
                'current': quote.get('current', 0),
                'percent': quote.get('percent', 0),
                'change': quote.get('change', 0),
                'open': quote.get('open', 0),
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'close': quote.get('close', 0),
                'last_close': quote.get('last_close', 0),
                'volume': quote.get('volume', 0),
                'amount': quote.get('amount', 0),
                'turnover_rate': quote.get('turnover_rate', 0),
                'market_capital': quote.get('market_capital', 0),
                'float_market_capital': quote.get('float_market_capital', 0),
                'pe_ttm': quote.get('pe_ttm', 0),
                'pe_lyr': quote.get('pe_lyr', 0),
                'pb': quote.get('pb', 0),
                'dividend_yield': quote.get('dividend_yield', 0),
                'total_shares': quote.get('total_shares', 0),
                'float_shares': quote.get('float_shares', 0)
            }

            return stock_detail

        except Exception as e:
            self.logger.error(f"获取股票详情失败 ({symbol}): {e}")
            raise

    def get_batch_details(self, symbols):
        """
        批量获取多只股票的详情
        Args:
            symbols: 股票代码列表

        Returns:
            list: 股票详情列表
        """
        self.logger.info(f"开始批量获取 {len(symbols)} 只股票详情")
        results = []

        for symbol in symbols:
            try:#某只股票失败则跳过，继续抓下一个，并返回日志
                detail = self.parse(symbol)
                if detail:
                    results.append(detail)
            except Exception as e:
                self.logger.warning(f"获取股票 {symbol} 详情失败: {e}")
                continue

        self.logger.info(f"批量获取完成，成功 {len(results)}/{len(symbols)} 只")
        return results
