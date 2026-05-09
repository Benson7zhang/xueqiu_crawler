"""
SQLite数据库存储模块
将爬取的股票榜单和股票详情保存到本地数据库文件。
"""

import os
import sqlite3
from utils.logger import setup_logger
import config


class SQLiteStorage:
    """
    SQLite存储类。

    SQLite 不需要单独安装数据库服务，适合本地调试。
    默认数据库文件：data/xueqiu.db
    """

    def __init__(self, db_path=None):
        """初始化SQLite连接并创建数据表。"""
        self.db_path = db_path or config.SQLITE_DB_PATH
        self.logger = setup_logger('SQLiteStorage')

        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        self.logger.info(f"使用SQLite数据库: {self.db_path}")

    def _create_tables(self):
        """创建股票榜单表和股票详情表。"""
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT,
                board TEXT,
                current REAL,
                percent REAL,
                change REAL,
                volume INTEGER,
                amount INTEGER,
                turnover_rate REAL,
                market_capital INTEGER,
                pe_ttm REAL,
                crawled_at TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_detail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT,
                current REAL,
                percent REAL,
                change REAL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                last_close REAL,
                volume INTEGER,
                amount INTEGER,
                turnover_rate REAL,
                market_capital INTEGER,
                float_market_capital INTEGER,
                pe_ttm REAL,
                pe_lyr REAL,
                pb REAL,
                dividend_yield REAL,
                total_shares INTEGER,
                float_shares INTEGER,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

    def save_stock_list(self, stock_list):
        """
        保存股票榜单数据。

        Args:
            stock_list: 股票列表，每一项是一个dict

        Returns:
            int: 保存条数
        """
        if not stock_list:
            self.logger.warning("股票列表为空，跳过保存")
            return 0

        sql = """
            INSERT INTO stock_list (
                symbol, name, board, current, percent, change, volume, amount,
                turnover_rate, market_capital, pe_ttm, crawled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [
            (
                item.get('symbol', ''),
                item.get('name', ''),
                item.get('board', ''),
                item.get('current', 0),
                item.get('percent', 0),
                item.get('change', 0),
                item.get('volume', 0),
                item.get('amount', 0),
                item.get('turnover_rate', 0),
                item.get('market_capital', 0),
                item.get('pe_ttm', 0),
                item.get('crawled_at', ''),
            )
            for item in stock_list
        ]

        self.connection.executemany(sql, rows)
        self.connection.commit()
        self.logger.info(f"股票列表已保存到SQLite (共 {len(rows)} 条)")
        return len(rows)

    def save_stock_details(self, stock_details):
        """
        保存股票详情数据。

        Args:
            stock_details: 股票详情列表，每一项是一个dict

        Returns:
            int: 保存条数
        """
        if not stock_details:
            self.logger.warning("股票详情为空，跳过保存")
            return 0

        sql = """
            INSERT INTO stock_detail (
                symbol, name, current, percent, change, open, high, low, close,
                last_close, volume, amount, turnover_rate, market_capital,
                float_market_capital, pe_ttm, pe_lyr, pb, dividend_yield,
                total_shares, float_shares
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [
            (
                item.get('symbol', ''),
                item.get('name', ''),
                item.get('current', 0),
                item.get('percent', 0),
                item.get('change', 0),
                item.get('open', 0),
                item.get('high', 0),
                item.get('low', 0),
                item.get('close', 0),
                item.get('last_close', 0),
                item.get('volume', 0),
                item.get('amount', 0),
                item.get('turnover_rate', 0),
                item.get('market_capital', 0),
                item.get('float_market_capital', 0),
                item.get('pe_ttm', 0),
                item.get('pe_lyr', 0),
                item.get('pb', 0),
                item.get('dividend_yield', 0),
                item.get('total_shares', 0),
                item.get('float_shares', 0),
            )
            for item in stock_details
        ]

        self.connection.executemany(sql, rows)
        self.connection.commit()
        self.logger.info(f"股票详情已保存到SQLite (共 {len(rows)} 条)")
        return len(rows)

    def close(self):
        """关闭数据库连接。"""
        if self.connection:
            self.connection.close()
            self.logger.info("SQLite数据库连接已关闭")
