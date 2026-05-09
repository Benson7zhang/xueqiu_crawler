"""
MySQL数据库存储模块
将爬取的股票榜单和股票详情保存到MySQL数据库。
"""

import re
import pymysql
from utils.logger import setup_logger
import config


IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z0-9_\u4e00-\u9fff]+$')
ALLOWED_CHARSETS = {'utf8mb4', 'utf8'}

STOCK_LIST_COLUMN_MAP = [
    ('id', '序号', 'INT AUTO_INCREMENT'),
    ('symbol', '股票代码', 'VARCHAR(20) NOT NULL'),
    ('name', '股票名称', 'VARCHAR(100)'),
    ('board', '榜单名称', 'VARCHAR(50)'),
    ('current', '当前价', 'DECIMAL(18, 4)'),
    ('percent', '涨跌幅', 'DECIMAL(18, 4)'),
    ('change', '涨跌额', 'DECIMAL(18, 4)'),
    ('volume', '成交量', 'BIGINT'),
    ('amount', '成交额', 'BIGINT'),
    ('turnover_rate', '换手率', 'DECIMAL(18, 4)'),
    ('market_capital', '总市值', 'BIGINT'),
    ('pe_ttm', '市盈率TTM', 'DECIMAL(18, 4)'),
    ('crawled_at', '抓取时间', 'VARCHAR(50)'),
    ('created_at', '入库时间', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
]

STOCK_DETAIL_COLUMN_MAP = [
    ('id', '序号', 'INT AUTO_INCREMENT'),
    ('symbol', '股票代码', 'VARCHAR(20) NOT NULL'),
    ('name', '股票名称', 'VARCHAR(100)'),
    ('current', '当前价', 'DECIMAL(18, 4)'),
    ('percent', '涨跌幅', 'DECIMAL(18, 4)'),
    ('change', '涨跌额', 'DECIMAL(18, 4)'),
    ('open', '开盘价', 'DECIMAL(18, 4)'),
    ('high', '最高价', 'DECIMAL(18, 4)'),
    ('low', '最低价', 'DECIMAL(18, 4)'),
    ('close', '收盘价', 'DECIMAL(18, 4)'),
    ('last_close', '昨收价', 'DECIMAL(18, 4)'),
    ('volume', '成交量', 'BIGINT'),
    ('amount', '成交额', 'BIGINT'),
    ('turnover_rate', '换手率', 'DECIMAL(18, 4)'),
    ('market_capital', '总市值', 'BIGINT'),
    ('float_market_capital', '流通市值', 'BIGINT'),
    ('pe_ttm', '市盈率TTM', 'DECIMAL(18, 4)'),
    ('pe_lyr', '市盈率LYR', 'DECIMAL(18, 4)'),
    ('pb', '市净率', 'DECIMAL(18, 4)'),
    ('dividend_yield', '股息率', 'DECIMAL(18, 4)'),
    ('total_shares', '总股本', 'BIGINT'),
    ('float_shares', '流通股本', 'BIGINT'),
    ('created_at', '入库时间', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
]


class MySQLStorage:
    """
    MySQL存储类。

    默认使用 config.MYSQL_CONFIG 中的连接信息：
    1. 先连接MySQL服务
    2. 自动创建数据库
    3. 自动创建 stock_list 和 stock_detail 两张表
    4. 保存榜单和详情数据
    """

    def __init__(self, db_config=None):
        """初始化MySQL存储。"""
        self.db_config = db_config or config.MYSQL_CONFIG
        self.logger = setup_logger('MySQLStorage')
        self.connection = None

        self._ensure_database()
        self._connect()
        self._create_tables()

    def _connect_server(self):
        """连接MySQL服务，不指定具体数据库，用于创建数据库。"""
        return pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            charset=self.db_config['charset']
        )

    def _validate_config(self):
        """校验会进入DDL语句的配置项。"""
        database = self.db_config['database']
        charset = self.db_config['charset']

        if not IDENTIFIER_PATTERN.match(database):
            raise ValueError("MYSQL_DATABASE 只能包含字母、数字、下划线或中文")
        if charset not in ALLOWED_CHARSETS:
            raise ValueError("MYSQL_CHARSET 只支持 utf8mb4 或 utf8")

    def _ensure_database(self):
        """如果数据库不存在，则自动创建。"""
        self._validate_config()
        database = self.db_config['database']
        charset = self.db_config['charset']

        try:
            connection = self._connect_server()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{database}` "
                        f"DEFAULT CHARACTER SET {charset}"
                    )
                connection.commit()
                self.logger.info(f"数据库已准备好: {database}")
            finally:
                connection.close()
        except Exception as e:
            self.logger.error(f"创建/检查数据库失败: {e}")
            raise

    def _connect(self):
        """连接具体业务数据库。"""
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset=self.db_config['charset']
            )
            self.logger.info("MySQL数据库连接成功")
        except Exception as e:
            self.logger.error(f"MySQL数据库连接失败: {e}")
            raise

    def _create_tables(self):
        """创建数据表，并把旧英文字段迁移为中文字段。"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_list (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        `股票代码` VARCHAR(20) NOT NULL,
                        `股票名称` VARCHAR(100),
                        `榜单名称` VARCHAR(50),
                        `当前价` DECIMAL(18, 4),
                        `涨跌幅` DECIMAL(18, 4),
                        `涨跌额` DECIMAL(18, 4),
                        `成交量` BIGINT,
                        `成交额` BIGINT,
                        `换手率` DECIMAL(18, 4),
                        `总市值` BIGINT,
                        `市盈率TTM` DECIMAL(18, 4),
                        `抓取时间` VARCHAR(50),
                        `入库时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_symbol (`股票代码`),
                        INDEX idx_created_at (`入库时间`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_detail (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        `股票代码` VARCHAR(20) NOT NULL,
                        `股票名称` VARCHAR(100),
                        `当前价` DECIMAL(18, 4),
                        `涨跌幅` DECIMAL(18, 4),
                        `涨跌额` DECIMAL(18, 4),
                        `开盘价` DECIMAL(18, 4),
                        `最高价` DECIMAL(18, 4),
                        `最低价` DECIMAL(18, 4),
                        `收盘价` DECIMAL(18, 4),
                        `昨收价` DECIMAL(18, 4),
                        `成交量` BIGINT,
                        `成交额` BIGINT,
                        `换手率` DECIMAL(18, 4),
                        `总市值` BIGINT,
                        `流通市值` BIGINT,
                        `市盈率TTM` DECIMAL(18, 4),
                        `市盈率LYR` DECIMAL(18, 4),
                        `市净率` DECIMAL(18, 4),
                        `股息率` DECIMAL(18, 4),
                        `总股本` BIGINT,
                        `流通股本` BIGINT,
                        `入库时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_symbol (`股票代码`),
                        INDEX idx_created_at (`入库时间`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                self._migrate_columns(cursor, 'stock_list', STOCK_LIST_COLUMN_MAP)
                self._migrate_columns(cursor, 'stock_detail', STOCK_DETAIL_COLUMN_MAP)

                self.connection.commit()
                self.logger.info("MySQL数据表创建/检查完成")
        except Exception as e:
            self.logger.error(f"创建MySQL数据表失败: {e}")
            raise

    def _quote_name(self, name):
        """给表名或字段名加反引号。"""
        if not IDENTIFIER_PATTERN.match(name):
            raise ValueError(f"非法表名或字段名: {name}")
        return f"`{name.replace('`', '``')}`"

    def _column_exists(self, cursor, table_name, column_name):
        """检查字段是否存在。"""
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema=%s AND table_name=%s AND column_name=%s
            """,
            (self.db_config['database'], table_name, column_name)
        )
        return cursor.fetchone()[0] > 0

    def _migrate_columns(self, cursor, table_name, column_map):
        """把旧英文字段改为中文字段，缺少的中文字段自动补齐。"""
        for old_name, chinese_name, column_type in column_map:
            self._validate_column_type(column_type)
            old_exists = self._column_exists(cursor, table_name, old_name)
            chinese_exists = self._column_exists(cursor, table_name, chinese_name)

            if old_exists and not chinese_exists:
                cursor.execute(
                    f"ALTER TABLE {self._quote_name(table_name)} "
                    f"CHANGE COLUMN {self._quote_name(old_name)} "
                    f"{self._quote_name(chinese_name)} {column_type}"
                )
                self.logger.info(
                    f"已把 {table_name}.{old_name} 改为 {chinese_name}"
                )
            elif not old_exists and not chinese_exists:
                self._ensure_column(cursor, table_name, chinese_name, column_type)

    def _ensure_column(self, cursor, table_name, column_name, column_type):
        """旧表缺少字段时自动补充。"""
        self._validate_column_type(column_type)
        if not self._column_exists(cursor, table_name, column_name):
            cursor.execute(
                f"ALTER TABLE {self._quote_name(table_name)} "
                f"ADD COLUMN {self._quote_name(column_name)} {column_type}"
            )
            self.logger.info(f"已为 {table_name} 补充字段: {column_name}")

    def _validate_column_type(self, column_type):
        """限制DDL字段类型来源，避免任意SQL片段进入DDL。"""
        allowed_prefixes = (
            'INT',
            'VARCHAR',
            'DECIMAL',
            'BIGINT',
            'TIMESTAMP',
        )
        if not column_type.startswith(allowed_prefixes):
            raise ValueError(f"非法字段类型: {column_type}")

    def save_stock_list(self, stock_list):
        """
        保存股票榜单数据。

        Args:
            stock_list: 股票列表数据

        Returns:
            int: 插入的记录数
        """
        if not stock_list:
            self.logger.warning("股票列表为空，跳过保存")
            return 0

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO stock_list
                    (`股票代码`, `股票名称`, `榜单名称`, `当前价`, `涨跌幅`, `涨跌额`,
                     `成交量`, `成交额`, `换手率`, `总市值`, `市盈率TTM`, `抓取时间`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                data = [
                    (
                        stock.get('symbol', ''),
                        stock.get('name', ''),
                        stock.get('board', ''),
                        stock.get('current', 0),
                        stock.get('percent', 0),
                        stock.get('change', 0),
                        stock.get('volume', 0),
                        stock.get('amount', 0),
                        stock.get('turnover_rate', 0),
                        stock.get('market_capital', 0),
                        stock.get('pe_ttm', 0),
                        stock.get('crawled_at', ''),
                    )
                    for stock in stock_list
                ]
                cursor.executemany(sql, data)
                self.connection.commit()
                self.logger.info(f"股票列表已保存到MySQL (共 {len(stock_list)} 条)")
                return len(stock_list)
        except Exception as e:
            self.logger.error(f"保存股票列表失败: {e}")
            self.connection.rollback()
            raise

    def save_stock_details(self, stock_details):
        """
        保存股票详情数据。

        Args:
            stock_details: 股票详情列表

        Returns:
            int: 插入的记录数
        """
        if not stock_details:
            self.logger.warning("股票详情为空，跳过保存")
            return 0

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO stock_detail
                    (`股票代码`, `股票名称`, `当前价`, `涨跌幅`, `涨跌额`, `开盘价`,
                     `最高价`, `最低价`, `收盘价`, `昨收价`, `成交量`, `成交额`,
                     `换手率`, `总市值`, `流通市值`, `市盈率TTM`, `市盈率LYR`,
                     `市净率`, `股息率`, `总股本`, `流通股本`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                data = [
                    (
                        detail.get('symbol', ''),
                        detail.get('name', ''),
                        detail.get('current', 0),
                        detail.get('percent', 0),
                        detail.get('change', 0),
                        detail.get('open', 0),
                        detail.get('high', 0),
                        detail.get('low', 0),
                        detail.get('close', 0),
                        detail.get('last_close', 0),
                        detail.get('volume', 0),
                        detail.get('amount', 0),
                        detail.get('turnover_rate', 0),
                        detail.get('market_capital', 0),
                        detail.get('float_market_capital', 0),
                        detail.get('pe_ttm', 0),
                        detail.get('pe_lyr', 0),
                        detail.get('pb', 0),
                        detail.get('dividend_yield', 0),
                        detail.get('total_shares', 0),
                        detail.get('float_shares', 0),
                    )
                    for detail in stock_details
                ]
                cursor.executemany(sql, data)
                self.connection.commit()
                self.logger.info(f"股票详情已保存到MySQL (共 {len(stock_details)} 条)")
                return len(stock_details)
        except Exception as e:
            self.logger.error(f"保存股票详情失败: {e}")
            self.connection.rollback()
            raise

    def close(self):
        """关闭数据库连接。"""
        if self.connection:
            self.connection.close()
            self.logger.info("MySQL数据库连接已关闭")
