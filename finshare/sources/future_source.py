# sources/future_source.py
"""
期货数据源实现

支持获取期货实时行情和历史K线数据。

数据源:
- 新浪期货: 实时行情
- 东方财富期货: 历史K线
"""

import re
import json
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict

from finshare.sources.base_source import BaseDataSource
from finshare.models.data_models import (
    HistoricalData,
    FutureData,
    FutureSnapshotData,
    FutureExchange,
    AdjustmentType,
    MarketType,
    SnapshotData,
)
from finshare.logger import logger


# 期货代码映射 (新浪格式 -> 标准格式)
FUTURE_CODE_MAP = {
    # 股指期货
    "IF": "IF",   # 沪深300股指
    "IH": "IH",   # 上证50股指
    "IC": "IC",   # 中证500股指
    # 金属期货
    "CU": "CU",   # 沪铜
    "AL": "AL",   # 沪铝
    "ZN": "ZN",   # 沪锌
    "PB": "PB",   # 沪铅
    "NI": "NI",   # 沪镍
    "AU": "AU",   # 沪金
    "AG": "AG",   # 沪银
    # 能源化工
    "RU": "RU",   # 沪胶
    "RU": "RU",   # 沪橡胶
    "FU": "FU",   # 沪燃油
    "RU": "RU",   # 天然橡胶
    "SC": "SC",   # 原油
    "TA": "TA",   # PTA
    "MA": "MA",   # 甲醇
    "FG": "FG",   # 玻璃
    "RS": "RS",   # 菜籽
    "RM": "RM",   # 菜粕
    "SR": "SR",   # 白糖
    "CF": "CF",   # 棉花
    "CY": "CY",   # 棉纱
    "AP": "AP",   # 苹果
    # 农产品
    "A": "A",     # 豆一
    "B": "B",     # 豆二
    "M": "M",     # 豆粕
    "Y": "Y",     # 豆油
    "P": "P",     # 棕榈油
    "L": "L",     # 聚乙烯
    "V": "V",     # 聚氯乙烯
    "J": "J",     # 焦炭
    "JM": "JM",   # 焦煤
    "I": "I",     # 铁矿石
    "J": "J",     # 螺纹钢
    "RB": "RB",   # 螺纹钢
    "HC": "HC",   # 热卷
    "SS": "SS",   # 不锈钢
}


def _get_exchange(code: str) -> FutureExchange:
    """根据期货代码判断交易所"""
    code_upper = code.upper()

    # 股指期货 (中金所)
    if code_upper.startswith(("IF", "IH", "IC", "TS", "TF", "T")):
        return FutureExchange.CFFEX

    # 金属/能源期货 (上期所)
    if code_upper.startswith(("CU", "AL", "ZN", "PB", "NI", "AU", "AG", "RU", "FU", "SC", "WR")):
        return FutureExchange.SHFE

    # 农产品/化工 (大商所)
    if code_upper.startswith(("A", "B", "M", "Y", "P", "L", "V", "J", "JM", "I", "RB", "HC", "SS", "EB", "PG")):
        return FutureExchange.DCE

    # 农产品/化工 (郑商所)
    if code_upper.startswith(("TA", "MA", "FG", "RS", "RM", "SR", "CF", "CY", "AP", "UR", "LR", "JR", "SM", "AP")):
        return FutureExchange.CZCE

    # 原油 (上期能源)
    if code_upper.startswith("SC"):
        return FutureExchange.INE

    return FutureExchange.SHFE


class FutureDataSource(BaseDataSource):
    """期货数据源实现"""

    def __init__(self):
        super().__init__("future")
        self.sina_base_url = "https://hq.sinajs.cn"
        self.eastmoney_base_url = "http://push2his.eastmoney.com"

        # 新浪API headers
        self.sina_headers = {
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "*/*",
            "Host": "hq.sinajs.cn",
        }

    def get_historical_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        adjustment: AdjustmentType = AdjustmentType.NONE,
    ) -> List[HistoricalData]:
        """
        获取期货历史K线数据

        Args:
            code: 期货合约代码 (如 IF2409, CU2409)
                  也支持简写: IF0 (当月连续)
            start_date: 开始日期
            end_date: 结束日期
            adjustment: 复权类型 (期货不支持，默认NONE)

        Returns:
            List[HistoricalData] 历史K线数据列表
        """
        try:
            # 解析期货代码
            future_code, contract_month = self._parse_future_code(code)

            # 新浪期货K线API
            # API: http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine
            url = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine"

            # 构建symbol (新浪使用小写，连续合约用0表示)
            symbol = f"{future_code.lower()}{contract_month if contract_month else '0'}"
            params = {"symbol": symbol}

            logger.debug(f"期货历史数据请求: {code}, {start_date} - {end_date}, symbol={symbol}")

            response_data = self._make_request(url, params)

            if not response_data:
                logger.warning(f"期货历史数据请求无响应: {code}")
                return []

            # 解析数据
            data = self._parse_sina_kline(response_data)

            if not data or not isinstance(data, list):
                logger.warning(f"期货历史数据解析失败: {code}")
                return []

            # 转换为HistoricalData
            historical_data = self._convert_to_historical(data, code)

            # 筛选日期范围
            filtered_data = [d for d in historical_data if start_date <= d.trade_date <= end_date]

            if filtered_data:
                logger.debug(f"期货历史数据获取成功: {code}, 共{len(filtered_data)}条")
            else:
                logger.warning(f"期货历史数据为空: {code}")

            return filtered_data

        except Exception as e:
            logger.error(f"获取期货历史数据失败 {code}: {e}")
            return []

    def get_future_snapshot(self, code: str) -> Optional[FutureSnapshotData]:
        """
        获取期货实时快照

        Args:
            code: 期货合约代码 (如 IF2409, CU2409)

        Returns:
            FutureSnapshotData 实时快照数据
        """
        try:
            # 解析期货代码
            future_code, contract_month = self._parse_future_code(code)

            # 新浪期货实时API
            url = f"{self.sina_base_url}/list=nf_{future_code}{contract_month}"

            response_data = self._make_request(url)

            if not response_data:
                return None

            snapshot = self._parse_sina_future_snapshot(response_data, code)

            if snapshot:
                logger.debug(f"期货快照获取成功: {code}")

            return snapshot

        except Exception as e:
            logger.error(f"获取期货快照失败 {code}: {e}")
            return None

    def get_batch_future_snapshots(self, codes: List[str]) -> Dict[str, FutureSnapshotData]:
        """
        批量获取期货实时快照

        Args:
            codes: 期货合约代码列表

        Returns:
            Dict[str, FutureSnapshotData] 代码 -> 快照数据
        """
        results = {}

        for code in codes:
            snapshot = self.get_future_snapshot(code)
            if snapshot:
                results[code] = snapshot

        return results

    # ============ 实现抽象方法 (返回 None，因为期货使用专门的 FutureSnapshotData) ============

    def get_snapshot_data(self, code: str) -> Optional[SnapshotData]:
        """
        获取交易快照数据 (期货不支持，返回 None)

        使用 get_future_snapshot 获取期货快照数据。
        """
        logger.warning("期货数据源不支持 get_snapshot_data，请使用 get_future_snapshot")
        return None

    def get_batch_snapshots(self, codes: List[str]) -> Dict[str, SnapshotData]:
        """
        批量获取快照数据 (期货不支持，返回空字典)

        使用 get_batch_future_snapshots 获取期货快照数据。
        """
        logger.warning("期货数据源不支持 get_batch_snapshots，请使用 get_batch_future_snapshots")
        return {}

    def _parse_future_code(self, code: str) -> tuple:
        """
        解析期货代码

        Args:
            code: 期货合约代码 (如 IF2409, IF0, cu2409, cu0)

        Returns:
            (期货品种代码, 合约月份)
            如: ("IF", "2409") 或 ("CU", "") (用于连续合约)
        """
        code = code.strip().upper()

        # 移除可能的交易所后缀
        for suffix in [".SHFE", ".CFFEX", ".DCE", ".CZCE", ".INE"]:
            code = code.replace(suffix, "")

        # 尝试提取品种代码和月份
        # 格式: IF2409, IF0, CU2409, CU
        match = re.match(r"^([A-Z]+)(\d*)$", code)

        if match:
            future_type = match.group(1)
            month = match.group(2)

            # 处理0、空或连续合约 (如 cu0, IF0)
            # Sina使用连续合约如 cu0, IF0
            if month in ("", "0", "00"):
                # Sina使用空字符串表示连续合约
                return future_type, ""

            return future_type, month

        # 如果无法解析，返回原代码
        return code, ""

    def _parse_sina_kline(self, response_data) -> List:
        """解析新浪期货K线数据

        新浪格式: [["2024-01-02", 3421.0, 3450.0, 3445.0, 3420.0, 3456.0], ...]
        [日期, 开盘, 最高, 最低, 收盘, 成交量]
        """
        try:
            # Sina返回的是直接的列表
            if isinstance(response_data, list):
                return response_data

            # 如果是字符串，尝试解析
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
                return data if isinstance(data, list) else []

            return []

        except Exception as e:
            logger.error(f"解析新浪K线失败: {e}")
            return []
            logger.error(f"解析东方财富K线失败: {e}")
            return []

    def _convert_to_historical(self, klines: List, code: str) -> List[HistoricalData]:
        """转换K线数据为HistoricalData

        Sina格式: [["2024-01-02", 3421.0, 3450.0, 3445.0, 3420.0, 3456.0], ...]
        [日期, 开盘, 最高, 最低, 收盘, 成交量]
        """
        historical_list = []

        for item in klines:
            try:
                # Sina格式是列表
                if not isinstance(item, (list, tuple)) or len(item) < 6:
                    continue

                trade_date_str = item[0]
                # 检查日期有效性
                if not trade_date_str or trade_date_str == "0000-00-00":
                    continue

                try:
                    trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue

                open_price = float(item[1]) if item[1] else 0
                high_price = float(item[2]) if item[2] else 0
                low_price = float(item[3]) if item[3] else 0
                close_price = float(item[4]) if item[4] else 0
                volume = float(item[5]) if item[5] else 0

                # Sina格式没有成交额，用 成交量*价格 估算
                amount = volume * close_price if close_price > 0 else 0

                historical_data = HistoricalData(
                    code=code,
                    trade_date=trade_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                    amount=amount,
                    adjust_factor=1.0,
                    market=MarketType.SH,  # 期货统一用SH
                    adjustment=AdjustmentType.NONE,
                    data_source=self.source_name,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                historical_list.append(historical_data)

            except (ValueError, TypeError, IndexError) as e:
                logger.debug(f"解析K线条目失败: {e}")
                continue

        return historical_list

    def _parse_sina_future_snapshot(self, content: str, code: str) -> Optional[FutureSnapshotData]:
        """
        解析新浪期货实时数据

        格式: var nf_IF2409="日期,开盘,最高,最低,最新,成交量,持仓量,...";
        """
        try:
            # 查找数据
            pattern = r'var nf_[A-Z]+\d+="(.*?)"'
            match = re.search(pattern, content)

            if not match:
                return None

            data_str = match.group(1)
            parts = data_str.split(",")

            if len(parts) < 7:
                return None

            # 解析数据
            # 0: 日期时间, 1: 开盘, 2: 最高, 3: 最低, 4: 最新, 5: 成交量, 6: 持仓量
            # 7: 买入价, 8: 卖出价, 9: 昨收, 10: 今开, 11: 最高, 12: 最低
            last_price = float(parts[4]) if parts[4] else 0
            volume = float(parts[5]) if parts[5] else 0
            open_interest = float(parts[6]) if parts[6] else 0
            bid_price = float(parts[7]) if len(parts) > 7 and parts[7] else 0
            ask_price = float(parts[8]) if len(parts) > 8 and parts[8] else 0
            prev_close = float(parts[9]) if len(parts) > 9 and parts[9] else 0
            day_open = float(parts[10]) if len(parts) > 10 and parts[10] else 0
            day_high = float(parts[11]) if len(parts) > 11 and parts[11] else 0
            day_low = float(parts[12]) if len(parts) > 12 and parts[12] else 0

            # 成交额
            amount = volume * last_price if last_price > 0 else 0

            snapshot = FutureSnapshotData(
                code=code,
                timestamp=datetime.now(),
                last_price=last_price,
                volume=volume,
                open_interest=open_interest,
                amount=amount,
                bid1_price=bid_price,
                ask1_price=ask_price,
                day_high=day_high,
                day_low=day_low,
                day_open=day_open,
                prev_close=prev_close,
                exchange=_get_exchange(code),
                data_source=self.source_name,
            )

            return snapshot

        except Exception as e:
            logger.error(f"解析新浪期货快照失败: {e}")
            return None


# 为了兼容旧代码，添加别名
FutureSource = FutureDataSource
