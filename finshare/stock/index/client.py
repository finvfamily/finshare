"""
IndexClient - 指数成分股 + PE/PB 估值历史客户端

提供指数成分股查询（东方财富）和估值历史数据（乐估乐股）。
"""

import pandas as pd
from typing import Optional

from finshare.stock.base_client import BaseClient
from finshare.logger import logger


LG_SYMBOL_MAP = {
    "上证指数": "000001.XSHG",
    "沪深300": "000300.XSHG",
    "中证500": "000905.XSHG",
    "中证1000": "000852.XSHG",
    "创业板指": "399006.XSHE",
    "上证50": "000016.XSHG",
    "深证成指": "399001.XSHE",
    "科创50": "000688.XSHG",
    "中证全指": "000985.XSHG",
    "中证800": "000906.XSHG",
}

# Also support lookup by code (without exchange suffix)
_CODE_TO_LG = {v.split(".")[0]: v for v in LG_SYMBOL_MAP.values()}


class IndexClient(BaseClient):
    """指数成分股 + PE/PB 估值历史客户端"""

    CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
    LG_PE_URL = "https://legulegu.com/api/stockdata/index-pe"
    LG_PB_URL = "https://legulegu.com/api/stockdata/index-pb"

    # Cache TTLs (seconds)
    TTL_CONSTITUENTS = 86400  # 24h — quarterly rebalance
    TTL_VALUATION = 3600       # 1h  — daily update

    def __init__(self):
        super().__init__("eastmoney_index")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_secid(self, index_code: str) -> str:
        """
        将指数代码转换为 EastMoney secid 格式。

        首位 0/3/9 → 0.{code}，其余 → 1.{code}
        """
        code = index_code.strip()
        first = code[0] if code else ""
        if first in ("0", "3", "9"):
            return f"0.{code}"
        return f"1.{code}"

    def _resolve_lg_symbol(self, symbol: str) -> Optional[str]:
        """
        将中文名称或代码映射到乐估乐股 symbol。

        支持：
        - 中文名称，如 "沪深300"
        - 纯数字代码，如 "000300"
        - 已包含交易所后缀，如 "000300.XSHG"
        """
        # Direct map by Chinese name
        if symbol in LG_SYMBOL_MAP:
            return LG_SYMBOL_MAP[symbol]

        # Already in legulegu format
        if ".XSHG" in symbol or ".XSHE" in symbol:
            return symbol

        # Lookup by numeric code
        code = symbol.strip()
        if code in _CODE_TO_LG:
            return _CODE_TO_LG[code]

        logger.warning(f"[eastmoney_index] 无法映射指数代码到乐估乐股 symbol: {symbol}")
        return None

    # ------------------------------------------------------------------
    # Private fetch methods
    # ------------------------------------------------------------------

    def _fetch_index_constituents(self, index_code: str) -> Optional[pd.DataFrame]:
        """从东方财富获取指数成分股"""
        secid = self._to_secid(index_code)
        logger.debug(f"获取指数成分股: {index_code} (secid={secid})")

        params = {
            "fs": f"b:{secid}",
            "fields": "f12,f14",
            "pz": 10000,
        }
        headers = {"Referer": "https://quote.eastmoney.com/"}
        data = self._make_request(self.CLIST_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            data_obj = data.get("data") or {}
            diff = data_obj.get("diff", []) if isinstance(data_obj, dict) else []
            if not diff:
                logger.warning(f"[eastmoney_index] 成分股列表为空: {index_code}")
                return None

            records = []
            for item in diff:
                raw_code = str(item.get("f12", ""))
                name = item.get("f14", "")
                fs_code = self._ensure_full_code(raw_code)
                records.append({"fs_code": fs_code, "name": name})

            df = pd.DataFrame(records)
            logger.info(f"获取指数成分股成功: {index_code}, {len(df)}只")
            return df
        except Exception as e:
            logger.error(f"解析指数成分股失败: {e}")
            return None

    def _fetch_index_constituents_csindex(self, index_code: str) -> Optional[pd.DataFrame]:
        """备用源：中证指数官网获取成分股"""
        headers = {
            "Referer": "https://www.csindex.com.cn/",
            "User-Agent": self.get_random_user_agent(),
        }
        try:
            response = self.session.get(
                f"https://www.csindex.com.cn/csindex-home/index-info/index-stocks?indexCode={index_code}",
                headers=headers, timeout=15
            )
            if response.status_code != 200:
                return None
            data = response.json()
            items = data.get("data", [])
            if not items:
                return None
            records = []
            for item in items:
                code = str(item.get("securityCode", ""))
                name = item.get("securityNameAbbr", "")
                fs_code = self._ensure_full_code(code)
                records.append({"fs_code": fs_code, "name": name})
            df = pd.DataFrame(records)
            logger.info(f"CSIndex 备用源获取成分股成功: {index_code}, {len(df)}只")
            return df
        except Exception as e:
            logger.warning(f"CSIndex 备用源失败: {e}")
            return None

    def _fetch_index_pe(self, symbol: str) -> Optional[pd.DataFrame]:
        """从乐估乐股获取指数 PE 历史"""
        lg_symbol = self._resolve_lg_symbol(symbol)
        if not lg_symbol:
            return None

        logger.debug(f"获取指数PE: {symbol} -> {lg_symbol}")

        params = {"token": "", "indexCode": lg_symbol}
        headers = {"Referer": "https://legulegu.com/stockdata/index-pe"}

        data = self._make_request(self.LG_PE_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            items = data if isinstance(data, list) else data.get("data", [])

            if not items:
                logger.warning(f"[eastmoney_index] PE 数据为空: {symbol}")
                return None

            records = []
            for item in items:
                records.append({
                    "date": pd.to_datetime(item["date"], unit="ms"),
                    "index_val": item.get("close") or item.get("indexValue") or item.get("index_val"),
                    "pe": item.get("pe"),
                    "pe_ttm": item.get("peTTM") or item.get("pe_ttm"),
                })

            df = pd.DataFrame(records)
            logger.info(f"获取指数PE成功: {symbol}, {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"解析指数PE失败: {e}")
            return None

    def _fetch_index_pb(self, symbol: str) -> Optional[pd.DataFrame]:
        """从乐估乐股获取指数 PB 历史"""
        lg_symbol = self._resolve_lg_symbol(symbol)
        if not lg_symbol:
            return None

        logger.debug(f"获取指数PB: {symbol} -> {lg_symbol}")

        params = {"token": "", "indexCode": lg_symbol}
        headers = {"Referer": "https://legulegu.com/stockdata/index-pb"}

        data = self._make_request(self.LG_PB_URL, params=params, headers=headers)

        if not data:
            return None

        try:
            items = data if isinstance(data, list) else data.get("data", [])

            if not items:
                logger.warning(f"[eastmoney_index] PB 数据为空: {symbol}")
                return None

            records = []
            for item in items:
                records.append({
                    "date": pd.to_datetime(item["date"], unit="ms"),
                    "index_val": item.get("close") or item.get("indexValue") or item.get("index_val"),
                    "pb": item.get("pb"),
                })

            df = pd.DataFrame(records)
            logger.info(f"获取指数PB成功: {symbol}, {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"解析指数PB失败: {e}")
            return None

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_index_constituents(self, index_code: str) -> pd.DataFrame:
        """获取指数成分股列表（带缓存 + CSIndex 备用源）"""
        cache_key = f"index_cons:{index_code}"
        result = self._cached_request(
            cache_key, self.TTL_CONSTITUENTS,
            lambda: self._fetch_index_constituents(index_code)
        )
        if result is None:
            # Backup: CSIndex
            logger.warning(f"东财指数成分股失败，尝试中证指数备用源: {index_code}")
            backup = self._fetch_index_constituents_csindex(index_code)
            if backup is not None and not backup.empty:
                self._cache.set(cache_key, backup, ttl=30)
                return backup
            return pd.DataFrame(columns=["fs_code", "name"])
        return result

    def get_index_pe(self, symbol: str) -> pd.DataFrame:
        """获取指数 PE 历史（带缓存）"""
        lg_symbol = self._resolve_lg_symbol(symbol)
        if not lg_symbol:
            return pd.DataFrame(columns=["date", "index_val", "pe", "pe_ttm"])
        cache_key = f"index_pe:{lg_symbol}"
        result = self._cached_request(
            cache_key, self.TTL_VALUATION,
            lambda: self._fetch_index_pe(symbol)
        )
        return result if result is not None else pd.DataFrame(columns=["date", "index_val", "pe", "pe_ttm"])

    def get_index_pb(self, symbol: str) -> pd.DataFrame:
        """获取指数 PB 历史（带缓存）"""
        lg_symbol = self._resolve_lg_symbol(symbol)
        if not lg_symbol:
            return pd.DataFrame(columns=["date", "index_val", "pb"])
        cache_key = f"index_pb:{lg_symbol}"
        result = self._cached_request(
            cache_key, self.TTL_VALUATION,
            lambda: self._fetch_index_pb(symbol)
        )
        return result if result is not None else pd.DataFrame(columns=["date", "index_val", "pb"])
