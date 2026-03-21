"""
ValuationClient - 全市场PB + 全球指数 + 全量行情 + ETF分类

提供A股全市场PB中位数历史、全球主要指数日线、A股全量实时行情及ETF分类数据。
"""

import pandas as pd

from finshare.stock.base_client import BaseClient
from finshare.logger import logger


GLOBAL_INDEX_MAP = {
    ".DJI": "100.DJIA", ".IXIC": "100.NDX", ".INX": "100.SPX",
    "DJI": "100.DJIA", "IXIC": "100.NDX", "SPX": "100.SPX",
    "HSI": "100.HSI", "HSTECH": "100.HSTECH", "HSCEI": "100.HSCEI",
}


class ValuationClient(BaseClient):
    """全市场PB + 全球指数 + 全量行情 + ETF分类客户端"""

    LG_MARKET_PB_URL = "https://legulegu.com/api/stockdata/market-pb"
    KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
    SINA_HQ_URL = "https://hq.sinajs.cn/list="

    # Cache TTLs (seconds)
    TTL_VALUATION = 3600       # 1h  — daily update
    TTL_SPOT = 5               # 5s  — real-time
    TTL_ETF_CLASS = 14400      # 4h  — weekly changes

    def __init__(self):
        super().__init__("valuation")

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_market_pb(self) -> pd.DataFrame:
        """
        获取A股全市场PB中位数历史（乐估乐股 API）。

        Returns:
            DataFrame 包含列:
            - date: 日期 (YYYY-MM-DD 字符串)
            - middlePB: PB中位数
            - quantileInRecent10YearsMiddlePB: 近10年分位数
            - close: 指数收盘价
        """
        empty = pd.DataFrame(columns=["date", "middlePB", "quantileInRecent10YearsMiddlePB", "close"])
        result = self._cached_request("market_pb", self.TTL_VALUATION, self._fetch_market_pb)
        return result if result is not None else empty

    def get_global_index_daily(self, symbol: str) -> pd.DataFrame:
        """
        获取全球指数日线数据（东方财富 API）。

        Args:
            symbol: 指数代号，如 "HSI", ".DJI", "SPX" 等

        Returns:
            DataFrame 包含列:
            - date: 日期
            - open: 开盘价
            - close: 收盘价
            - high: 最高价
            - low: 最低价
            - volume: 成交量
        """
        empty = pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])

        secid = GLOBAL_INDEX_MAP.get(symbol.upper(), GLOBAL_INDEX_MAP.get(symbol))
        if not secid:
            logger.warning(f"[valuation] 未知的全球指数代号: {symbol}")
            return empty

        cache_key = f"global_index:{secid}"
        result = self._cached_request(
            cache_key, self.TTL_VALUATION,
            lambda: self._fetch_global_index_daily(secid, symbol),
        )
        return result if result is not None else empty

    def get_stock_spot(self) -> pd.DataFrame:
        """获取A股全量实时行情（含PE/PB/市值/换手率），带多级降级"""
        empty = pd.DataFrame(columns=[
            "code", "name", "price", "change_pct",
            "pe_ttm", "pb", "turnover_rate",
            "total_mv", "circ_mv", "change_pct_60d", "change_pct_ytd",
        ])
        cache_key = "stock_spot"

        # 1. Try fresh cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # 2. Try primary source (fast retry: 1 retry, 1s delay)
        result = self._fetch_stock_spot_primary()
        if result is not None and not result.empty:
            # Save code list for Sina backup use
            self._cache.set("stock_code_list", result["code"].tolist(), ttl=86400)
            self._cache.set(cache_key, result, ttl=self.TTL_SPOT)
            return result

        # 3. Try stale cache
        stale = self._cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("[valuation] stock_spot 返回过期缓存")
            return stale

        # 4. Try Sina backup
        logger.warning("东财全量行情失败，尝试新浪备用源")
        backup = self._fetch_stock_spot_sina()
        if backup is not None and not backup.empty:
            self._cache.set(cache_key, backup, ttl=30)
            return backup

        return empty

    def get_etf_classification(self) -> pd.DataFrame:
        """
        获取ETF基金分类数据。

        Returns:
            DataFrame 包含列:
            - fs_code: ETF代码
            - fund_type: 基金类型 (debt/qdii/money/equity)
            - name: 基金名称
        """
        empty = pd.DataFrame(columns=["fs_code", "fund_type", "name"])
        result = self._cached_request("etf_classification", self.TTL_ETF_CLASS, self._fetch_etf_classification)
        return result if result is not None else empty

    # ------------------------------------------------------------------
    # Private fetch methods
    # ------------------------------------------------------------------

    def _fetch_market_pb(self):
        """从乐估乐股获取全市场PB中位数历史"""
        params = {"token": ""}
        headers = {"Referer": "https://legulegu.com/stockdata/market-pb"}

        logger.debug("获取A股全市场PB中位数历史")
        data = self._make_request(self.LG_MARKET_PB_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            items = data.get("data", []) if isinstance(data, dict) else data

            if not items:
                logger.warning("[valuation] 全市场PB数据为空")
                return None

            records = []
            for item in items:
                ts = item.get("date")
                if ts is not None:
                    date_str = pd.to_datetime(ts, unit="ms").strftime("%Y-%m-%d")
                else:
                    date_str = None
                records.append({
                    "date": date_str,
                    "middlePB": item.get("middlePB"),
                    "quantileInRecent10YearsMiddlePB": item.get("quantileInRecent10YearsMiddlePB"),
                    "close": item.get("close"),
                })

            df = pd.DataFrame(records)
            logger.info(f"获取全市场PB成功: {len(df)}条")
            return df
        except Exception as e:
            logger.error(f"[valuation] 解析全市场PB失败: {e}")
            return None

    def _fetch_global_index_daily(self, secid: str, symbol: str):
        """从东方财富获取全球指数日线"""
        params = {
            "secid": secid,
            "klt": 101,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "beg": "19700101",
            "end": "20500101",
        }
        headers = {"Referer": "https://quote.eastmoney.com/"}

        logger.debug(f"获取全球指数日线: {symbol} (secid={secid})")
        data = self._make_request(self.KLINE_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            data_obj = data.get("data") or {}
            klines = data_obj.get("klines", []) if isinstance(data_obj, dict) else []

            if not klines:
                logger.warning(f"[valuation] 全球指数日线数据为空: {symbol}")
                return None

            records = []
            for kline in klines:
                parts = kline.split(",")
                if len(parts) < 6:
                    continue
                records.append({
                    "date": parts[0],
                    "open": float(parts[1]) if parts[1] else None,
                    "close": float(parts[2]) if parts[2] else None,
                    "high": float(parts[3]) if parts[3] else None,
                    "low": float(parts[4]) if parts[4] else None,
                    "volume": float(parts[5]) if parts[5] else None,
                })

            df = pd.DataFrame(records)
            logger.info(f"获取全球指数日线成功: {symbol}, {len(df)}条")
            return df
        except Exception as e:
            logger.error(f"[valuation] 解析全球指数日线失败: {e}")
            return None

    def _fetch_stock_spot_primary(self):
        """从东方财富获取全量行情（使用快速重试）"""
        params = {
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
            "fields": "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f20,f21,f23,f24,f25,f115",
            "pn": 1,
            "pz": 10000,
            "fltt": 2,
        }
        headers = {"Referer": "https://quote.eastmoney.com/"}

        logger.debug("获取A股全量实时行情")
        data = self._make_request(self.CLIST_URL, params=params, headers=headers, fast=True)

        if not data:
            return None

        try:
            data_obj = data.get("data") or {}
            diff = data_obj.get("diff", []) if isinstance(data_obj, dict) else []
            if not diff:
                logger.warning("[valuation] 全量行情数据为空")
                return None

            records = []
            for item in diff:
                records.append({
                    "code": str(item.get("f12", "")),
                    "name": item.get("f14", ""),
                    "price": item.get("f2"),
                    "change_pct": item.get("f3"),
                    "pe_ttm": item.get("f9"),
                    "pb": item.get("f23"),
                    "turnover_rate": item.get("f8"),
                    "total_mv": item.get("f20"),
                    "circ_mv": item.get("f21"),
                    "change_pct_60d": item.get("f24"),
                    "change_pct_ytd": item.get("f25"),
                })

            df = pd.DataFrame(records)
            logger.info(f"获取A股全量行情成功: {len(df)}只")
            return df
        except Exception as e:
            logger.error(f"[valuation] 解析全量行情失败: {e}")
            return None

    def _fetch_stock_spot_sina(self):
        """备用源：新浪行情批量查询"""
        import re

        try:
            # Get code list from dedicated cache (set by successful primary fetches)
            codes = self._cache.get_stale("stock_code_list")
            if not codes:
                logger.warning("无法获取股票代码列表，Sina 备用源放弃")
                return None

            records = []
            batch_size = 80

            for i in range(0, len(codes), batch_size):
                batch = codes[i:i + batch_size]
                sina_codes = []
                for code in batch:
                    code_str = str(code)
                    if code_str.startswith("6") or code_str.startswith("5") or code_str.startswith("9"):
                        sina_codes.append(f"sh{code_str}")
                    else:
                        sina_codes.append(f"sz{code_str}")

                url = self.SINA_HQ_URL + ",".join(sina_codes)
                headers = {"Referer": "https://finance.sina.com.cn/"}

                try:
                    response = self.session.get(url, headers=headers, timeout=10)
                    if response.status_code != 200:
                        continue

                    text = response.text
                    for line in text.strip().split("\n"):
                        if not line or "=" not in line:
                            continue
                        match = re.search(r'hq_str_(\w+)="(.+)"', line)
                        if not match:
                            continue

                        sina_code = match.group(1)
                        fields = match.group(2).split(",")
                        if len(fields) < 32:
                            continue

                        num_code = sina_code[2:]  # Remove sh/sz prefix

                        records.append({
                            "code": num_code,
                            "name": fields[0],
                            "price": float(fields[3]) if fields[3] else None,
                            "change_pct": round(
                                (float(fields[3]) - float(fields[2])) / float(fields[2]) * 100, 2
                            ) if fields[3] and fields[2] and float(fields[2]) > 0 else None,
                            "pe_ttm": None,
                            "pb": None,
                            "turnover_rate": None,
                            "total_mv": None,
                            "circ_mv": None,
                            "change_pct_60d": None,
                            "change_pct_ytd": None,
                        })

                except Exception as e:
                    logger.debug(f"Sina 批次请求失败: {e}")
                    continue

            if not records:
                return None

            df = pd.DataFrame(records)
            logger.info(f"Sina 备用源获取行情成功: {len(df)}只")
            return df

        except Exception as e:
            logger.warning(f"Sina 备用源整体失败: {e}")
            return None

    def _fetch_etf_classification(self):
        """从东方财富获取ETF分类数据"""
        params = {
            "fs": "b:MK0021+b:MK0022+b:MK0023+b:MK0024",
            "fields": "f12,f14,f3",
            "pn": 1,
            "pz": 10000,
            "fltt": 2,
        }
        headers = {"Referer": "https://quote.eastmoney.com/"}

        logger.debug("获取ETF基金分类")
        data = self._make_request(self.CLIST_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            data_obj = data.get("data") or {}
            diff = data_obj.get("diff", []) if isinstance(data_obj, dict) else []

            if not diff:
                logger.warning("[valuation] ETF分类数据为空")
                return None

            records = []
            for item in diff:
                name = item.get("f14", "")
                fund_type = self._classify_etf(name)
                records.append({
                    "fs_code": str(item.get("f12", "")),
                    "fund_type": fund_type,
                    "name": name,
                })

            df = pd.DataFrame(records)
            logger.info(f"获取ETF分类成功: {len(df)}只")
            return df
        except Exception as e:
            logger.error(f"[valuation] 解析ETF分类失败: {e}")
            return None

    def _classify_etf(self, name: str) -> str:
        """根据ETF名称分类"""
        if any(kw in name for kw in ["债", "利率"]):
            return "debt"
        if any(kw in name for kw in ["QDII", "纳斯达克", "标普"]):
            return "qdii"
        if "货币" in name:
            return "money"
        return "equity"
