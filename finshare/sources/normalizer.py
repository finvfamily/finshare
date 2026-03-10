"""
数据标准化器 - 统一多数据源格式

功能:
- 股票代码统一: 各种格式 → 000001.SZ
- 价格单位统一: 分/厘 → 元
- 成交量单位统一: 股 → 手
- 字段名称统一: close/Close/CLOSE → close_price
- 日期格式统一: 各种格式 → YYYY-MM-DD
"""

import re
from datetime import datetime, date
from typing import Any, Dict, Optional
from finshare.logger import logger


class DataNormalizer:
    """
    数据标准化器

    将不同数据源的原始数据转换为统一格式。
    """

    # 价格除数表（转换为元）
    PRICE_DIVISORS = {
        "eastmoney": 100,       # 分 → 元
        "eastmoney_fund": 1000, # 厘 → 元 (ETF/LOF)
        "tencent": 1000,        # 厘 → 元
        "sina": 100,            # 分 → 元
        "baostock": 1,          # 已经是元
        "tdx": 100,             # 分 → 元
        "default": 1,
    }

    # 成交量除数表（转换为手）
    VOLUME_DIVISORS = {
        "eastmoney": 1,         # 手
        "tencent": 1,           # 手
        "sina": 100,            # 股 → 手
        "baostock": 1,          # 手
        "tdx": 100,             # 股 → 手
        "default": 100,         # 默认股 → 手
    }

    # 字段名映射表
    FIELD_MAPPINGS = {
        # 代码
        "code": "fs_code",
        "fs_code": "fs_code",
        "stock_code": "fs_code",
        "symbol": "fs_code",
        # 日期/时间
        "trade_date": "trade_date",
        "date": "trade_date",
        "datetime": "trade_time",
        "trade_time": "trade_time",
        "time": "trade_time",
        # 价格
        "close": "close_price",
        "close_price": "close_price",
        "closeprice": "close_price",
        "price": "close_price",
        "last_price": "close_price",
        "open": "open_price",
        "open_price": "open_price",
        "openprice": "open_price",
        "high": "high_price",
        "high_price": "high_price",
        "highprice": "high_price",
        "low": "low_price",
        "low_price": "low_price",
        "lowprice": "low_price",
        # 成交量
        "vol": "volume",
        "volume": "volume",
        "volumn": "volume",
        "amount": "amount",
        # 盘口
        "bid_price": "bid1_price",
        "bid": "bid1_price",
        "ask_price": "ask1_price",
        "ask": "ask1_price",
        "bid_volume": "bid1_volume",
        "bid_vol": "bid1_volume",
        "ask_volume": "ask1_volume",
        "ask_vol": "ask1_volume",
    }

    def __init__(self):
        pass

    # ============ 股票代码标准化 ============

    def normalize_code(self, code: Any, source: str = "default") -> str:
        """
        标准化股票代码

        输入格式:
        - SZ000001, SH600519, BJ430001
        - sz000001, sh600519
        - 000001.SZ, 600001.SH
        - sz.000001, sh.600519 (BaoStock格式)

        输出格式: 000001.SZ, 600001.SH, 430001.BJ
        """
        if not code:
            return ""

        # 转换为字符串并去除空格
        code = str(code).strip().upper()

        # 已经是标准格式 (000001.SZ, 600001.SH)
        if "." in code:
            parts = code.split(".")
            if len(parts) == 2:
                # parts[0] = 市场代码, parts[1] = 证券代码 (如 600519.SH)
                # 或者 parts[0] = 证券代码, parts[1] = 市场代码 (如 sz.600519)
                part0, part1 = parts[0].upper(), parts[1].upper()

                # 判断哪个是市场代码
                if part0 in ("SZ", "SH", "BJ", "HK", "US") and part1.isdigit():
                    # 格式: SH600519
                    return f"{part1}.{part0}"
                elif part1 in ("SZ", "SH", "BJ", "HK", "US") and part0.isdigit():
                    # 格式: 600519.SH
                    return f"{part0}.{part1}"
                elif part0.isdigit() and part1.isdigit():
                    # 都是数字，无法判断
                    pass

        # 处理 BaoStock 格式 (sz.000001) - 无数字前缀
        prefix_map = {"SZ": "SZ", "SH": "SH", "BJ": "BJ", "HK": "HK", "US": "US"}
        for prefix, market in prefix_map.items():
            if code.startswith(prefix):
                num_code = code[len(prefix):]
                if num_code.isdigit():
                    return f"{num_code}.{market}"

        # 纯数字代码
        if code.isdigit():
            first = code[0]
            if first in ["6", "5"]:
                return f"{code}.SH"
            elif first in ["0", "1", "2", "3"]:
                return f"{code}.SZ"
            elif first == "9":
                if code.startswith("90"):
                    return f"{code}.SH"
                else:
                    return f"{code}.BJ"

        logger.warning(f"无法标准化股票代码: {code}")
        return code

    # ============ 价格标准化 ============

    def normalize_price(
        self,
        price: Any,
        source: str = "default",
        field: str = "price",
    ) -> float:
        """
        标准化价格（统一转为元）

        Args:
            price: 价格值
            source: 数据源
            field: 字段名（用于判断是否为基金等特殊品种）

        Returns:
            元为单位的价格
        """
        if price is None or price == "":
            return 0.0

        try:
            price_float = float(price)
        except (ValueError, TypeError):
            logger.warning(f"价格转换失败: {price}")
            return 0.0

        # 获取除数
        if source == "eastmoney" and "fund" in field.lower():
            divisor = self.PRICE_DIVISORS.get("eastmoney_fund", 1000)
        else:
            divisor = self.PRICE_DIVISORS.get(source, self.PRICE_DIVISORS["default"])

        # 转换为元
        return round(price_float / divisor, 2)

    # ============ 成交量标准化 ============

    def normalize_volume(
        self,
        volume: Any,
        source: str = "default",
    ) -> float:
        """
        标准化成交量（统一转为手）

        Args:
            volume: 成交量
            source: 数据源

        Returns:
            手为单位的成交量
        """
        if volume is None or volume == "":
            return 0.0

        try:
            volume_float = float(volume)
        except (ValueError, TypeError):
            logger.warning(f"成交量转换失败: {volume}")
            return 0.0

        # 获取除数
        divisor = self.VOLUME_DIVISORS.get(source, self.VOLUME_DIVISORS["default"])

        # 转换为手
        return round(volume_float / divisor, 2)

    # ============ 成交额标准化 ============

    def normalize_amount(
        self,
        amount: Any,
        source: str = "default",
    ) -> float:
        """
        标准化成交额

        统一转为元（千元输入转元）
        """
        if amount is None or amount == "":
            return 0.0

        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            return 0.0

        # 千元 → 元
        return round(amount_float * 1000, 2)

    # ============ 日期/时间标准化 ============

    def normalize_date(self, date_value: Any) -> str:
        """
        标准化日期为 YYYY-MM-DD 格式

        输入格式:
        - 20240101
        - 2024-01-01
        - 2024/01/01
        - datetime/date 对象
        """
        if not date_value:
            return ""

        # 已经是 date/datetime 对象
        if isinstance(date_value, (datetime, date)):
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            return date_value.strftime("%Y-%m-%d")

        # 字符串
        date_str = str(date_value).strip()

        # 尝试多种格式
        for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d%H%M%S"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"日期格式无法解析: {date_value}")
        return date_str

    def normalize_datetime(self, datetime_value: Any) -> str:
        """
        标准化时间为 YYYY-MM-DD HH:MM:SS 格式
        """
        if not datetime_value:
            return ""

        # 已经是 datetime 对象
        if isinstance(datetime_value, datetime):
            return datetime_value.strftime("%Y-%m-%d %H:%M:%S")

        # 字符串
        dt_str = str(datetime_value).strip()

        # 尝试多种格式
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S", "%Y-%m-%d", "%Y%m%d"]:
            try:
                dt = datetime.strptime(dt_str, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        logger.warning(f"时间格式无法解析: {datetime_value}")
        return dt_str

    # ============ 字段名标准化 ============

    def normalize_field_name(self, field_name: str) -> str:
        """
        标准化字段名

        close → close_price
        vol → volume
        """
        field_lower = field_name.lower()

        # 精确匹配
        if field_lower in self.FIELD_MAPPINGS:
            return self.FIELD_MAPPINGS[field_lower]

        # 部分匹配
        for old_name, new_name in self.FIELD_MAPPINGS.items():
            if old_name in field_lower:
                return new_name

        return field_name

    # ============ 批量标准化 ============

    def normalize_record(
        self,
        record: Dict[str, Any],
        source: str = "default",
    ) -> Dict[str, Any]:
        """
        标准化单条记录

        Args:
            record: 原始记录
            source: 数据源

        Returns:
            标准化后的记录
        """
        normalized = {}

        for key, value in record.items():
            # 标准化字段名
            new_key = self.normalize_field_name(key)

            # 根据字段名标准化值
            if "price" in new_key or new_key in ("close", "open", "high", "low"):
                normalized[new_key] = self.normalize_price(value, source, key)
            elif new_key == "volume":
                normalized[new_key] = self.normalize_volume(value, source)
            elif new_key == "amount":
                normalized[new_key] = self.normalize_amount(value, source)
            elif "date" in new_key and "time" not in new_key:
                normalized[new_key] = self.normalize_date(value)
            elif "time" in new_key:
                normalized[new_key] = self.normalize_datetime(value)
            elif new_key == "fs_code":
                normalized[new_key] = self.normalize_code(value, source)
            else:
                normalized[new_key] = value

        return normalized

    def normalize_records(
        self,
        records: list,
        source: str = "default",
    ) -> list:
        """
        标准化多条记录
        """
        return [self.normalize_record(r, source) for r in records]


# 全局标准化器实例
_normalizer = None


def get_normalizer() -> DataNormalizer:
    """获取全局标准化器"""
    global _normalizer
    if _normalizer is None:
        _normalizer = DataNormalizer()
    return _normalizer
