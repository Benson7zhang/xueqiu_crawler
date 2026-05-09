"""
CSV存储模块
将爬取的数据保存为CSV文件
"""

import os
import pandas as pd
from datetime import datetime
from utils.logger import setup_logger
import config


STOCK_LIST_COLUMNS = {
    'symbol': '股票代码',
    'name': '股票名称',
    'board': '榜单名称',
    'current': '当前价',
    'percent': '涨跌幅',
    'change': '涨跌额',
    'volume': '成交量',
    'amount': '成交额',
    'turnover_rate': '换手率',
    'market_capital': '总市值',
    'pe_ttm': '市盈率TTM',
    'crawled_at': '抓取时间',
}

STOCK_DETAIL_COLUMNS = {
    'symbol': '股票代码',
    'name': '股票名称',
    'current': '当前价',
    'percent': '涨跌幅',
    'change': '涨跌额',
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'last_close': '昨收价',
    'volume': '成交量',
    'amount': '成交额',
    'turnover_rate': '换手率',
    'market_capital': '总市值',
    'float_market_capital': '流通市值',
    'pe_ttm': '市盈率TTM',
    'pe_lyr': '市盈率LYR',
    'pb': '市净率',
    'dividend_yield': '股息率',
    'total_shares': '总股本',
    'float_shares': '流通股本',
}


class CSVStorage:
    """
    CSV存储类
    负责将数据保存为CSV格式文件
    """

    def __init__(self, output_dir=None):
        """
        初始化CSV存储

        Args:
            output_dir: 输出目录，默认使用配置中的CSV_OUTPUT_DIR
        """
        self.output_dir = output_dir or config.CSV_OUTPUT_DIR
        self.logger = setup_logger('CSVStorage')

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"创建输出目录: {self.output_dir}")

    def _get_file_path(self, filename):
        """
        获取完整的文件路径

        Args:
            filename: 文件名

        Returns:
            str: 完整文件路径
        """
        return os.path.join(self.output_dir, filename)

    def _build_dataframe(self, rows, column_names):
        """按固定顺序整理字段，并把表头改成中文。"""
        df = pd.DataFrame(rows)
        ordered_columns = [name for name in column_names if name in df.columns]
        other_columns = [name for name in df.columns if name not in column_names]
        df = df[ordered_columns + other_columns]
        return df.rename(columns=column_names)

    def save_stock_list(self, stock_list, filename=None):
        """
        保存股票列表数据
        Args:
            stock_list: 股票列表数据
            filename: 文件名，默认使用时间戳命名

        Returns:
            str: 保存的文件路径
        """
        if not stock_list:
            self.logger.warning("股票列表为空，跳过保存")
            return None

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'stock_list_{timestamp}.csv'

        file_path = self._get_file_path(filename)

        try:
            df = self._build_dataframe(stock_list, STOCK_LIST_COLUMNS)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"股票列表已保存: {file_path} (共 {len(stock_list)} 条)")
            return file_path
        except Exception as e:
            self.logger.error(f"保存股票列表失败: {e}")
            raise

    def save_stock_details(self, stock_details, filename=None):
        """
        保存股票详情数据

        Args:
            stock_details: 股票详情列表
            filename: 文件名，默认使用时间戳命名

        Returns:
            str: 保存的文件路径
        """
        if not stock_details:
            self.logger.warning("股票详情为空，跳过保存")
            return None

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'stock_details_{timestamp}.csv'

        file_path = self._get_file_path(filename)

        try:
            df = self._build_dataframe(stock_details, STOCK_DETAIL_COLUMNS)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"股票详情已保存: {file_path} (共 {len(stock_details)} 条)")
            return file_path
        except Exception as e:
            self.logger.error(f"保存股票详情失败: {e}")
            raise

    def append_to_csv(self, data, filename):
        """
        追加数据到已存在的CSV文件

        Args:
            data: 要追加的数据（列表或DataFrame）
            filename: 目标文件名

        Returns:
            str: 文件路径
        """
        file_path = self._get_file_path(filename)

        try:
            # 转换为DataFrame
            if not isinstance(data, pd.DataFrame):
                df = pd.DataFrame(data)
            else:
                df = data

            # 检查文件是否存在
            if os.path.exists(file_path):
                # 追加模式
                df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
                self.logger.info(f"数据已追加到: {file_path} (追加 {len(df)} 条)")
            else:
                # 新建文件
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"新建文件并保存: {file_path} (共 {len(df)} 条)")

            return file_path
        except Exception as e:
            self.logger.error(f"追加数据失败: {e}")
            raise
