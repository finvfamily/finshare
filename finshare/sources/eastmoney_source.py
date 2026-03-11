# sources/eastmoney_source.py (完整代码)
import json
import time
from datetime import date, datetime
from typing import List, Optional, Dict

from finshare.models.data_models import HistoricalData, SnapshotData, AdjustmentType, MarketType, MinuteData
from finshare.logger import logger
from finshare.sources.base_source import BaseDataSource


class EastMoneyDataSource(BaseDataSource):
    """东方财富数据源实现"""

    def __init__(self):
        super().__init__("eastmoney")
        self.base_url = "https://push2.eastmoney.com"
        self.historical_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        self.snapshot_url = "https://push2.eastmoney.com/api/qt/stock/get"
        self.batch_url = "https://push2.eastmoney.com/api/qt/ulist.np/get"

        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://quote.eastmoney.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://quote.eastmoney.com",
        }

    def get_historical_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        adjustment: AdjustmentType = AdjustmentType.NONE,
    ) -> List[HistoricalData]:
        """获取东方财富历史数据"""
        try:
            # 确保使用完整代码
            full_code = self._ensure_full_code(code)

            # 转换复权类型为东方财富参数
            adjust_type = self._convert_adjustment_type(adjustment)

            # 构建请求参数
            secid = self._convert_to_secid(full_code)
            params = {
                "secid": secid,
                "klt": 101,  # 日线
                "fqt": adjust_type,  # 复权类型
                "beg": start_date.strftime("%Y%m%d"),
                "end": end_date.strftime("%Y%m%d"),
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "_": str(int(time.time() * 1000)),
            }

            logger.debug(f"东方财富历史数据请求参数: {params}")

            # 使用基类的 _make_request 方法
            response = self._make_request(self.historical_url, params)

            if not response or response.get("data") is None:
                logger.warning(f"东方财富历史数据请求失败: {full_code}")
                return []

            data = response["data"]
            if not data or "klines" not in data:
                logger.warning(f"东方财富历史数据为空: {full_code}")
                return []

            historical_data = self._parse_eastmoney_historical_data(
                data["klines"], full_code, adjustment, data.get("name")
            )

            if historical_data:
                logger.debug(
                    f"东方财富历史数据获取成功: {full_code}, 共{len(historical_data)}条数据"
                )
            else:
                logger.warning(f"东方财富历史数据解析后为空: {full_code}")

            return historical_data

        except Exception as e:
            error_msg = f"获取东方财富历史数据失败 {code}: {e}"
            logger.error(error_msg)
            return []

    def _parse_eastmoney_historical_data(
        self, klines: List[str], code: str, adjustment: AdjustmentType, name: str = None
    ) -> List[HistoricalData]:
        """解析东方财富历史数据格式"""
        historical_list = []

        # 确保使用完整代码
        full_code = self._ensure_full_code(code)

        for kline in klines:
            try:
                # 东方财富格式: "2023-12-01,12.34,12.56,12.12,12.45,1234567,123456789"
                parts = kline.split(",")
                if len(parts) < 6:
                    continue

                trade_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
                open_price = float(parts[1]) if parts[1] else 0.0
                close_price = float(parts[2]) if parts[2] else 0.0
                high_price = float(parts[3]) if parts[3] else 0.0
                low_price = float(parts[4]) if parts[4] else 0.0
                volume = float(parts[5]) if parts[5] else 0.0
                amount = float(parts[6]) if len(parts) > 6 and parts[6] else 0.0

                # 换手率可能在后面字段
                turnover_rate = float(parts[7]) if len(parts) > 7 and parts[7] else 0.0

                # 复权因子（需要从其他接口获取）
                adjust_factor = 1.0

                historical_data = HistoricalData(
                    code=full_code,
                    trade_date=trade_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                    amount=amount,
                    adjust_factor=adjust_factor,
                    turnover_rate=turnover_rate,
                    market=self._get_market_type(full_code),
                    adjustment=adjustment,
                    data_source=self.source_name,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                historical_list.append(historical_data)

            except (ValueError, TypeError, IndexError) as e:
                logger.debug(f"解析东方财富历史数据条目失败: {e}")
                continue

        return historical_list

    def get_snapshot_data(self, code: str) -> Optional[SnapshotData]:
        """获取东方财富实时快照数据"""
        try:
            # 确保使用完整代码
            full_code = self._ensure_full_code(code)

            secid = self._convert_to_secid(full_code)

            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100,f101,f102,f103,f104,f105,f106,f107,f108,f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200,f201,f202,f203,f204,f205,f206,f207,f208,f209,f210,f211,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f250",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "invt": 2,
                "_": str(int(time.time() * 1000)),
            }

            response = self._make_request(self.snapshot_url, params)

            if not response or response.get("data") is None:
                logger.warning(f"东方财富快照数据请求失败: {full_code}")
                return None

            data = response["data"]
            snapshot = self._parse_eastmoney_snapshot(data, full_code)

            if snapshot:
                logger.debug(f"东方财富快照数据获取成功: {full_code}")

            return snapshot

        except Exception as e:
            error_msg = f"获取东方财富快照数据失败 {code}: {e}"
            logger.error(error_msg)
            return None

    def _parse_eastmoney_snapshot(self, data: Dict, code: str) -> Optional[SnapshotData]:
        """解析东方财富快照数据"""
        try:
            # 确保使用完整代码
            full_code = self._ensure_full_code(code)

            # 根据证券类型确定价格除数
            # ETF/LOF/基金的价格单位是厘（/1000），股票是分（/100）
            price_divisor = self._get_price_divisor(full_code)

            # 解析字段
            current_price = data.get("f43", 0) / price_divisor
            pre_close = data.get("f60", 0) / price_divisor
            open_price = data.get("f46", 0) / price_divisor
            high_price = data.get("f44", 0) / price_divisor
            low_price = data.get("f45", 0) / price_divisor
            volume = data.get("f47", 0)  # 成交量（手）
            amount = data.get("f48", 0)  # 成交额
            bid_price = data.get("f9", 0) / price_divisor
            ask_price = data.get("f10", 0) / price_divisor
            bid_volume = data.get("f13", 0)  # 买一量
            ask_volume = data.get("f12", 0)  # 卖一量

            # 获取时间戳
            update_time = data.get("f168", "")
            if update_time:
                try:
                    # 格式: "2023-12-01 15:00:00"
                    timestamp = datetime.strptime(update_time, "%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            # 市场状态
            market_status = data.get("f84", 0)
            is_trading = market_status == 1

            snapshot = SnapshotData(
                code=full_code,
                timestamp=timestamp,
                last_price=current_price,
                volume=volume,  # 单位：手
                amount=amount,
                bid1_price=bid_price,
                ask1_price=ask_price,
                bid1_volume=bid_volume,
                ask1_volume=ask_volume,
                day_high=high_price,
                day_low=low_price,
                day_open=open_price,
                prev_close=pre_close,
                is_trading=is_trading,
                market=self._get_market_type(full_code),
                data_source=self.source_name,
            )

            return snapshot

        except Exception as e:
            logger.error(f"解析东方财富快照数据失败 {code}: {e}")
            return None

    def get_batch_snapshots(self, codes: List[str]) -> Dict[str, SnapshotData]:
        """批量获取东方财富快照数据"""
        results = {}

        # 确保使用完整代码
        full_codes = [self._ensure_full_code(code) for code in codes]

        # 东方财富API支持批量查询
        max_batch_size = 500  # 东方财富支持较大的批量

        for i in range(0, len(full_codes), max_batch_size):
            batch = full_codes[i : i + max_batch_size]

            # 转换为secid格式
            secids = [self._convert_to_secid(code) for code in batch]
            secid_str = ",".join(secids)

            params = {
                "fltt": 2,
                "secids": secid_str,
                "fields": "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45,f46,f48,f49,f47,f50,f57,f58,f59,f60,f61,f168,f169,f170,f171,f172,f265,f266,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f277,f278,f279,f280,f281,f282,f283,f284,f285,f286,f287,f288,f289,f290,f291,f292,f293,f294,f295,f296,f297,f298,f299,f300,f301,f302,f303,f304,f305,f306,f307,f308,f309,f310,f311,f312,f313,f314,f315,f316,f317,f318,f319,f320,f321,f322,f323,f324,f325,f326,f327,f328,f329,f330,f331,f332,f333,f334,f335,f336,f337,f338,f339,f340,f341,f342,f343,f344,f345,f346,f347,f348,f349,f350,f351,f352,f353,f354,f355,f356,f357,f358,f359,f360,f361,f362,f363,f364,f365,f366,f367,f368,f369,f370,f371,f372,f373,f374,f375,f376,f377,f378,f379,f380,f381,f382,f383,f384,f385,f386,f387,f388,f389,f390,f391,f392,f393,f394,f395,f396,f397,f398,f399,f400,f401,f402,f403,f404,f405,f406,f407,f408,f409,f410,f411,f412,f413,f414,f415,f416,f417,f418,f419,f420,f421,f422,f423,f424,f425,f426,f427,f428,f429,f430,f431,f432,f433,f434,f435,f436,f437,f438,f439,f440,f441,f442,f443,f444,f445,f446,f447,f448,f449,f450,f451,f452,f453,f454,f455,f456,f457,f458,f459,f460,f461,f462,f463,f464,f465,f466,f467,f468,f469,f470,f471,f472,f473,f474,f475,f476,f477,f478,f479,f480,f481,f482,f483,f484,f485,f486,f487,f488,f489,f490,f491,f492,f493,f494,f495,f496,f497,f498,f499,f500",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "_": str(int(time.time() * 1000)),
            }

            try:
                response = self._make_request(self.batch_url, params)

                if response and response.get("data") and response["data"].get("diff"):
                    batch_results = self._parse_eastmoney_batch_snapshots(
                        response["data"]["diff"], batch
                    )
                    results.update(batch_results)

                    logger.debug(f"东方财富批量快照获取: {len(batch_results)}/{len(batch)} 成功")

                # 避免请求过快
                time.sleep(5)

            except Exception as e:
                logger.error(f"东方财富批量快照获取失败: {e}")

        return results

    def _parse_eastmoney_batch_snapshots(
        self, diff_data: List[Dict], codes: List[str]
    ) -> Dict[str, SnapshotData]:
        """解析东方财富批量快照数据"""
        results = {}

        for item in diff_data:
            try:
                raw_code = item.get("f12", "")
                if not raw_code:
                    continue

                # 确保代码是完整格式
                code = self._ensure_full_code(raw_code)

                # 确保在请求的代码列表中
                if code not in codes:
                    continue

                # 构建快照数据
                snapshot = self._parse_eastmoney_batch_item(item, code)
                if snapshot:
                    results[code] = snapshot

            except Exception as e:
                logger.debug(f"解析东方财富批量快照条目失败: {e}")
                continue

        return results

    def _parse_eastmoney_batch_item(self, item: Dict, code: str) -> Optional[SnapshotData]:
        """解析批量快照中的单个条目"""
        try:
            # 确保使用完整代码
            full_code = self._ensure_full_code(code)

            current_price = item.get("f2", 0)  # 当前价
            pre_close = item.get("f18", 0)  # 昨收
            open_price = item.get("f17", 0)  # 今开
            high_price = item.get("f15", 0)  # 最高
            low_price = item.get("f16", 0)  # 最低
            volume = item.get("f5", 0)  # 成交量（手）
            amount = item.get("f6", 0)  # 成交额

            # 买一卖一数据
            bid_price = item.get("f9", 0)
            ask_price = item.get("f10", 0)
            bid_volume = item.get("f13", 0)
            ask_volume = item.get("f12", 0)

            # 时间戳
            update_time = item.get("f168", "")
            if update_time:
                try:
                    timestamp = datetime.strptime(update_time, "%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            snapshot = SnapshotData(
                code=full_code,
                timestamp=timestamp,
                last_price=current_price,
                volume=volume,  # 单位：手
                amount=amount,
                bid1_price=bid_price,
                ask1_price=ask_price,
                bid1_volume=bid_volume,
                ask1_volume=ask_volume,
                day_high=high_price,
                day_low=low_price,
                day_open=open_price,
                prev_close=pre_close,
                is_trading=current_price > 0,
                market=self._get_market_type(full_code),
                data_source=self.source_name,
            )

            return snapshot

        except Exception as e:
            logger.debug(f"解析批量快照条目失败 {code}: {e}")
            return None

    def _convert_to_secid(self, code: str) -> str:
        """转换为东方财富secid格式

        支持的输入格式:
        - SZ000001, SH600519 (旧格式)
        - 000001.SZ, 600001.SH
        - 000001, 600001 (纯数字)
        """
        # 标准化代码
        full_code = self._ensure_full_code(code)

        # 处理标准格式 (000001.SZ)
        if "." in full_code:
            parts = full_code.split(".")
            if len(parts) == 2:
                num_code = parts[0]
                market_str = parts[1].upper()

                if market_str == "SH":
                    market = 1
                    return f"{market}.{num_code}"
                elif market_str == "SZ":
                    market = 0
                    return f"{market}.{num_code}"
                elif market_str == "BJ":
                    market = 0
                    return f"{market}.{num_code}"

        # 判断市场 (旧格式 SZ000001)
        if full_code.startswith("SH"):
            market = 1  # 沪市
            clean_code = full_code[2:]
        elif full_code.startswith("SZ"):
            market = 0  # 深市
            clean_code = full_code[2:]
        elif full_code.startswith("BJ"):
            market = 0  # 北交所（深市代码）
            clean_code = full_code[2:]
        elif full_code.startswith("HK"):
            market = 116  # 港股
            clean_code = full_code[2:]
        elif full_code.startswith("US"):
            market = 105  # 美股
            clean_code = full_code[2:]
        else:
            # 根据数字判断
            clean_code = full_code.replace("SH", "").replace("SZ", "").replace("BJ", "")
            if clean_code and clean_code[0].isdigit():
                first_digit = clean_code[0]
                if first_digit in ["6", "5"]:
                    market = 1  # 沪市
                elif first_digit in ["0", "1", "2", "3"]:
                    market = 0  # 深市
                elif first_digit == "9":
                    if clean_code.startswith("90"):
                        market = 1  # 沪市（可转债）
                    else:
                        market = 0  # 北交所
                else:
                    market = 1  # 默认沪市
            else:
                market = 1  # 默认沪市

        return f"{market}.{clean_code}"

    def _convert_adjustment_type(self, adjustment: AdjustmentType) -> int:
        """转换复权类型为东方财富参数"""
        mapping = {
            AdjustmentType.NONE: 0,  # 不复权
            AdjustmentType.PREVIOUS: 1,  # 前复权
            AdjustmentType.POST: 2,  # 后复权
        }
        return mapping.get(adjustment, 0)

    def _get_price_divisor(self, code: str) -> int:
        """
        根据证券类型获取价格除数

        东方财富API返回的价格单位：
        - 股票：分（需要除以100）
        - ETF/LOF/基金：厘（需要除以1000）
        """
        full_code = self._ensure_full_code(code)
        clean_code = full_code.replace("SH", "").replace("SZ", "").replace("BJ", "")

        if not clean_code:
            return 100

        # ETF/LOF/基金代码规则：
        # 深圳：15xxxx (ETF), 16xxxx (LOF)
        # 上海：50xxxx (LOF), 51xxxx (ETF), 52xxxx, 56xxxx, 58xxxx, 59xxxx
        fund_prefixes = ("15", "16", "50", "51", "52", "56", "58", "59")

        if clean_code.startswith(fund_prefixes):
            return 1000  # ETF/LOF/基金用厘

        return 100  # 股票用分

    def _get_market_type(self, code: str) -> MarketType:
        """根据代码判断市场类型"""
        # 确保使用完整代码
        full_code = self._ensure_full_code(code)

        if full_code.startswith("SH"):
            return MarketType.SH
        elif full_code.startswith("SZ"):
            return MarketType.SZ
        elif full_code.startswith("BJ"):
            return MarketType.BJ
        elif full_code.startswith("HK"):
            return MarketType.HK
        elif full_code.startswith("US"):
            return MarketType.US
        else:
            # 根据数字判断
            clean_code = full_code.replace("SH", "").replace("SZ", "").replace("BJ", "")
            if clean_code and clean_code[0].isdigit():
                first_digit = clean_code[0]
                if first_digit in ["6", "5"]:
                    return MarketType.SH
                elif first_digit in ["0", "1", "2", "3"]:
                    return MarketType.SZ
                elif first_digit == "9":
                    if clean_code.startswith("90"):
                        return MarketType.SH
                    else:
                        return MarketType.BJ

        return MarketType.SH

    def _get_full_code(self, code: str) -> str:
        """获取完整代码（添加市场前缀）- 保持向后兼容"""
        return self._ensure_full_code(code)

    # ============ 分钟线数据接口 ============

    def get_minutely_data(
        self,
        code: str,
        start: datetime,
        end: datetime,
        freq: int = 5,
        adjustment: AdjustmentType = AdjustmentType.NONE,
    ) -> List[MinuteData]:
        """
        获取分钟K线数据

        Args:
            code: 股票代码 (支持 000001.SZ, SZ000001, 000001 等格式)
            start: 开始时间
            end: 结束时间
            freq: 频率 (1/5/15/30/60 分钟)
            adjustment: 复权类型

        Returns:
            分钟线数据列表
        """
        try:
            # 确保使用完整代码
            full_code = self._ensure_full_code(code)

            # 转换复权类型
            adjust_type = self._convert_adjustment_type(adjustment)

            # 东方财富分钟线参数
            # klt: 1=1分钟, 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟
            klt_map = {1: 1, 5: 5, 15: 15, 30: 30, 60: 60}
            klt = klt_map.get(freq, 5)

            # secid 转换
            secid = self._convert_to_secid(full_code)

            # 东方财富分钟线接口使用特殊的时间格式
            # beg: 0 表示从最近开始获取，end 使用时间戳格式（毫秒）
            # 计算结束时间戳
            if end:
                end_ts = int(end.timestamp() * 1000)
            else:
                end_ts = int(datetime.now().timestamp() * 1000)

            # 构建请求参数
            params = {
                "secid": secid,
                "klt": klt,  # 分钟线频率
                "fqt": adjust_type,  # 复权类型
                "beg": "0",  # 从最近开始
                "end": str(end_ts),
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "_": str(int(time.time() * 1000)),
            }

            logger.debug(f"东方财富分钟线请求参数: {params}")

            # 发送请求
            response = self._make_request(self.historical_url, params)

            if not response or response.get("data") is None:
                logger.warning(f"东方财富分钟线请求失败: {full_code}")
                return []

            data = response["data"]
            if not data or "klines" not in data:
                logger.warning(f"东方财富分钟线数据为空: {full_code}")
                return []

            # 解析分钟线数据
            minute_data = self._parse_minutely_data(
                data["klines"], full_code, freq
            )

            if minute_data:
                logger.debug(
                    f"东方财富分钟线获取成功: {full_code}, "
                    f"freq={freq}min, 共{len(minute_data)}条数据"
                )
            else:
                logger.warning(f"东方财富分钟线解析后为空: {full_code}")

            return minute_data

        except Exception as e:
            error_msg = f"获取东方财富分钟线失败 {code}: {e}"
            logger.error(error_msg)
            return []

    def _parse_minutely_data(
        self,
        klines: List[str],
        code: str,
        freq: int,
    ) -> List[MinuteData]:
        """解析东方财富分钟线数据格式"""
        minute_list = []

        # 确保使用标准格式代码
        fs_code = self._ensure_full_code(code)

        # 获取价格除数
        price_divisor = self._get_price_divisor(code)

        for kline in klines:
            try:
                # 东方财富分钟线格式: "2024-01-09 09:30:00,12.34,12.56,12.12,12.45,1234567,123456789"
                # 格式: 时间,开盘,收盘,最高,最低,成交量,成交额
                parts = kline.split(",")
                if len(parts) < 6:
                    continue

                # 解析时间 - 东方财富返回 "2024-01-09 09:35" 或 "2024-01-09 09:35:00"
                time_str = parts[0]
                # 尝试多种时间格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                    try:
                        dt = datetime.strptime(time_str, fmt)
                        trade_time = dt.strftime("%Y%m%d%H%M%S")
                        break
                    except ValueError:
                        continue
                else:
                    # 无法解析则跳过
                    logger.debug(f"无法解析时间格式: {time_str}")
                    continue

                # 解析价格（注意：东方财富返回的是元，不是分）
                open_price = float(parts[1]) if parts[1] else 0.0
                close_price = float(parts[2]) if parts[2] else 0.0
                high_price = float(parts[3]) if parts[3] else 0.0
                low_price = float(parts[4]) if parts[4] else 0.0

                # 成交量（东方财富分钟线返回的是股）
                volume = int(parts[5]) if parts[5] else 0

                # 成交额
                amount = float(parts[6]) if len(parts) > 6 and parts[6] else 0.0

                minute = MinuteData(
                    fs_code=fs_code,
                    trade_time=trade_time,
                    open=open_price,
                    close=close_price,
                    high=high_price,
                    low=low_price,
                    volume=volume,
                    amount=amount,
                    frequency=str(freq),
                    data_source=self.source_name,
                )
                minute_list.append(minute)

            except (ValueError, TypeError, IndexError) as e:
                logger.debug(f"解析东方财富分钟线数据条目失败: {e}")
                continue

        return minute_list

    # ============ 证券列表接口 ============

    def get_stock_list(self, market: str = "all", limit: int = 0) -> List[dict]:
        """
        获取A股股票列表

        Args:
            market: 市场类型 (all: 全部, sh: 上海, sz: 深圳)
            limit: 限制返回数量，0表示获取全部

        Returns:
            股票列表，每只股票包含代码、名称等信息

        Examples:
            >>> source = EastMoneyDataSource()
            >>> stocks = source.get_stock_list()
            >>> print(f"共有 {len(stocks)} 只股票")
        """
        try:
            # 东方财富股票列表API
            url = "http://28.push2.eastmoney.com/api/qt/clist/get"

            # 确定市场参数
            if market == "sh":
                fs_param = "m:1+t:23,m:1+t:80"  # 上海主板
            elif market == "sz":
                fs_param = "m:0+t:6,m:0+t:80"  # 深圳主板
            else:
                fs_param = "m:0+t:6,m:0+t:80,m:1+t:23,m:1+t:80"  # 全部

            # 获取所有数据（分页获取）
            all_stocks = []
            page = 1
            page_size = 5000  # 每次最多获取5000条

            while True:
                params = {
                    "pn": page,
                    "pz": page_size,
                    "po": 1,
                    "np": 1,
                    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": fs_param,
                    "fields": "f1,f2,f3,f4,f5,f6,f7,f12,f13,f14,f15,f16,f17,f18",
                }

                response_data = self._make_request(url, params)

                if not response_data:
                    break

                stocks = self._parse_stock_list(response_data)
                if not stocks:
                    break

                all_stocks.extend(stocks)

                # 检查是否需要继续获取
                if limit > 0 and len(all_stocks) >= limit:
                    all_stocks = all_stocks[:limit]
                    break

                # 如果返回数据少于page_size，说明已经是最后一页
                if len(stocks) < page_size:
                    break

                page += 1

            logger.info(f"获取股票列表成功: {len(all_stocks)} 只")
            return all_stocks

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def get_etf_list(self, limit: int = 0) -> List[dict]:
        """
        获取ETF基金列表

        Args:
            limit: 限制返回数量，0表示获取全部

        Returns:
            ETF列表，每只ETF包含代码、名称等信息
        """
        try:
            url = "http://28.push2.eastmoney.com/api/qt/clist/get"

            # 获取所有数据（分页获取）
            all_etfs = []
            page = 1
            page_size = 5000

            while True:
                params = {
                    "pn": page,
                    "pz": page_size,
                    "po": 1,
                    "np": 1,
                    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": "b:MK0021",  # ETF基金
                    "fields": "f1,f2,f3,f4,f5,f6,f7,f12,f13,f14,f15,f16,f17,f18",
                }

                response_data = self._make_request(url, params)

                if not response_data:
                    break

                etfs = self._parse_stock_list(response_data)
                if not etfs:
                    break

                all_etfs.extend(etfs)

                if limit > 0 and len(all_etfs) >= limit:
                    all_etfs = all_etfs[:limit]
                    break

                if len(etfs) < page_size:
                    break

                page += 1

            logger.info(f"获取ETF列表成功: {len(all_etfs)} 只")
            return all_etfs

        except Exception as e:
            logger.error(f"获取ETF列表失败: {e}")
            return []

    def get_lof_list(self, limit: int = 0) -> List[dict]:
        """
        获取LOF基金列表

        Args:
            limit: 限制返回数量，0表示获取全部

        Returns:
            LOF列表，每只LOF包含代码、名称等信息
        """
        try:
            url = "http://28.push2.eastmoney.com/api/qt/clist/get"

            # 获取所有数据（分页获取）
            all_lofs = []
            page = 1
            page_size = 5000

            while True:
                params = {
                    "pn": page,
                    "pz": page_size,
                    "po": 1,
                    "np": 1,
                    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": "b:MK0023",  # LOF基金
                    "fields": "f1,f2,f3,f4,f5,f6,f7,f12,f13,f14,f15,f16,f17,f18",
                }

                response_data = self._make_request(url, params)

                if not response_data:
                    break

                lofs = self._parse_stock_list(response_data)
                if not lofs:
                    break

                all_lofs.extend(lofs)

                if limit > 0 and len(all_lofs) >= limit:
                    all_lofs = all_lofs[:limit]
                    break

                if len(lofs) < page_size:
                    break

                page += 1

            logger.info(f"获取LOF列表成功: {len(all_lofs)} 只")
            return all_lofs

        except Exception as e:
            logger.error(f"获取LOF列表失败: {e}")
            return []

    def get_future_list(self) -> List[dict]:
        """
        获取期货列表

        Returns:
            期货列表
        """
        try:
            url = "http://push2.eastmoney.com/api/qt/clist/get"

            # 期货筛选
            params = {
                "pn": 1,
                "pz": 500,
                "po": 1,
                "np": 1,
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2,
                "invt": 2,
                "fid": "f3",
                "fs": "f:2,f:3,f:4,f:5,f:6,f:7,f:8,f:9,f:10,f:11,f:12,f:13,f:14,f:15,f:16,f:17,f:18,f:19,f:20,f:21,f:22,f:23,f:24,f:25,f:26,f:27,f:28,f:29,f:30,f:31,f:32,f:33,f:34,f:35,f:36,f:37,f:38,f:39,f:40,f:41,f:42,f:43,f:44,f:45,f:46,f:47,f:48,f:49,f:50",
                "fields": "f12,f13,f14",  # 代码, 市场, 名称
            }

            response_data = self._make_request(url, params)

            if not response_data:
                logger.warning("期货列表请求无响应")
                return []

            return self._parse_future_list(response_data)

        except Exception as e:
            logger.error(f"获取期货列表失败: {e}")
            return []

    def _parse_stock_list(self, response_data) -> List[dict]:
        """解析股票/ETF/LOF列表"""
        try:
            if isinstance(response_data, str):
                data = json.loads(response_data)
            else:
                data = response_data

            if data.get("data") is None:
                return []

            diff = data["data"].get("diff", [])
            results = []

            for item in diff:
                try:
                    stock_info = {
                        "code": item.get("f12"),          # 代码
                        "name": item.get("f14"),          # 名称
                        "market": item.get("f13"),        # 市场
                        "price": item.get("f2"),         # 最新价
                        "change_pct": item.get("f3"),    # 涨跌幅
                        "change": item.get("f4"),        # 涨跌额
                        "volume": item.get("f5"),        # 成交量
                        "amount": item.get("f6"),        # 成交额
                        "open": item.get("f17"),         # 开盘价
                        "high": item.get("f15"),         # 最高价
                        "low": item.get("f16"),          # 最低价
                        "close": item.get("f2"),         # 收盘价
                        "prev_close": item.get("f18"),   # 昨收价
                    }
                    results.append(stock_info)
                except Exception as e:
                    logger.debug(f"解析股票条目失败: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"解析股票列表失败: {e}")
            return []

    def _parse_future_list(self, response_data) -> List[dict]:
        """解析期货列表"""
        try:
            if isinstance(response_data, str):
                data = json.loads(response_data)
            else:
                data = response_data

            if data.get("data") is None:
                return []

            diff = data["data"].get("diff", [])
            results = []

            for item in diff:
                try:
                    future_info = {
                        "code": item.get("f12"),     # 代码
                        "name": item.get("f14"),     # 名称
                        "market": item.get("f13"),   # 市场
                    }
                    results.append(future_info)
                except Exception as e:
                    logger.debug(f"解析期货条目失败: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"解析期货列表失败: {e}")
            return []
