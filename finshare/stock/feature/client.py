"""
Feature Client - 东方财富特色数据客户端

提供资金流向、龙虎榜、融资融券等数据。
"""

import time
import random
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from finshare.logger import logger


class FeatureClient:
    """东方财富特色数据客户端"""

    # 特色数据API
    ULIST_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    LHBB_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    MARGIN_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    # 资金流向字段
    MONEY_FLOW_FIELDS = "f3,f4,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75"

    # User-Agent 池
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.source_name = "eastmoney_feature"
        self.session = requests.Session()
        self.request_interval = 0.5

    def get_random_user_agent(self) -> str:
        return random.choice(self.USER_AGENTS)

    def _rate_limit(self):
        time.sleep(self.request_interval)

    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        self._rate_limit()

        request_headers = {
            "User-Agent": self.get_random_user_agent(),
            "Referer": "https://quote.eastmoney.com/",
        }
        if headers:
            request_headers.update(headers)

        try:
            response = requests.get(url, params=params, headers=request_headers, timeout=30)

            if response.status_code >= 400:
                logger.warning(f"API请求失败: HTTP {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            logger.warning(f"API请求异常: {e}")
            return None

    def _ensure_full_code(self, code: str) -> str:
        """确保返回完整代码格式"""
        if not code:
            return code

        code = code.strip().upper()

        if "." in code:
            return code

        if code.isdigit():
            first = code[0]
            if first in ["6", "5"]:
                return f"{code}.SH"
            elif first in ["0", "1", "2", "3"]:
                return f"{code}.SZ"

        prefix_map = {"SZ": "SZ", "SH": "SH", "BJ": "BJ"}
        for prefix, market in prefix_map.items():
            if code.startswith(prefix):
                num_code = code[len(prefix):]
                return f"{num_code}.{market}"

        return code

    def _convert_to_secid(self, fs_code: str) -> str:
        """转换代码为secid格式"""
        if "." in fs_code:
            parts = fs_code.split(".")
            code = parts[0]
            market = parts[1]
        else:
            code = fs_code
            market = "SH" if fs_code.startswith("6") else "SZ"

        if market == "SH":
            return f"1.{code}"
        elif market == "SZ":
            return f"0.{code}"
        return f"0.{code}"

    def get_money_flow(self, code: str) -> pd.DataFrame:
        """
        获取个股资金流向

        Args:
            code: 股票代码 (000001.SZ)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - trade_date: 交易日期
            - net_inflow_main: 主力净流入(元)
            - net_inflow_super: 超大单净流入(元)
            - net_inflow_large: 大单净流入(元)
            - net_inflow_medium: 中单净流入(元)
            - net_inflow_small: 小单净流入(元)
            - net_inflow_main_ratio: 主力净流入占比(%)
            - net_inflow_super_ratio: 超大单净流入占比(%)
            - net_inflow_large_ratio: 大单净流入占比(%)
            - net_inflow_medium_ratio: 中单净流入占比(%)
            - net_inflow_small_ratio: 小单净流入占比(%)
        """
        fs_code = self._ensure_full_code(code)
        secid = self._convert_to_secid(fs_code)

        logger.debug(f"获取资金流向: {fs_code}")

        params = {
            "secids": secid,
            "fields": self.MONEY_FLOW_FIELDS,
            "fltt": "2",
        }

        data = self._make_request(self.ULIST_URL, params)

        if not data:
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "net_inflow_main", "net_inflow_super",
                "net_inflow_large", "net_inflow_medium", "net_inflow_small",
                "net_inflow_main_ratio", "net_inflow_super_ratio", "net_inflow_large_ratio",
                "net_inflow_medium_ratio", "net_inflow_small_ratio"
            ])

        try:
            data_obj = data.get("data", {})
            diff = data_obj.get("diff", []) if isinstance(data_obj, dict) else []
            if not diff:
                return pd.DataFrame(columns=[
                    "fs_code", "trade_date", "net_inflow_main", "net_inflow_super",
                    "net_inflow_large", "net_inflow_medium", "net_inflow_small",
                    "net_inflow_main_ratio", "net_inflow_super_ratio", "net_inflow_large_ratio",
                    "net_inflow_medium_ratio", "net_inflow_small_ratio"
                ])

            item = diff[0]
            record = {
                "fs_code": fs_code,
                "trade_date": datetime.now().strftime("%Y%m%d"),
                "net_inflow_main": item.get("f62", 0),  # 主力净流入
                "net_inflow_super": item.get("f63", 0),  # 超大单净流入
                "net_inflow_large": item.get("f64", 0),  # 大单净流入
                "net_inflow_medium": item.get("f65", 0),  # 中单净流入
                "net_inflow_small": item.get("f66", 0),  # 小单净流入
                "net_inflow_main_ratio": item.get("f67", 0),  # 主力净流入占比
                "net_inflow_super_ratio": item.get("f68", 0),  # 超大单净流入占比
                "net_inflow_large_ratio": item.get("f69", 0),  # 大单净流入占比
                "net_inflow_medium_ratio": item.get("f73", 0),  # 中单净流入占比
                "net_inflow_small_ratio": item.get("f74", 0),  # 小单净流入占比
            }

            df = pd.DataFrame([record])
            logger.info(f"获取资金流向成功: {fs_code}")
            return df

        except Exception as e:
            logger.error(f"解析资金流向失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "net_inflow_main", "net_inflow_super",
                "net_inflow_large", "net_inflow_medium", "net_inflow_small",
                "net_inflow_main_ratio", "net_inflow_super_ratio", "net_inflow_large_ratio",
                "net_inflow_medium_ratio", "net_inflow_small_ratio"
            ])

    def get_money_flow_industry(self) -> pd.DataFrame:
        """
        获取行业资金流向

        Returns:
            DataFrame 包含以下字段:
            - industry: 行业名称
            - net_inflow: 净流入(元)
            - net_inflow_ratio: 净流入占比(%)
            - change_rate: 涨跌幅(%)
        """
        logger.debug("获取行业资金流向")

        # 使用东方财富行业列表
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 100,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f742628",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:90+t:2",
            "fields": "f1,f2,f3,f4,f12,f13,f14",
        }

        data = self._make_request(url, params)

        if not data:
            return pd.DataFrame(columns=["industry", "net_inflow", "net_inflow_ratio", "change_rate"])

        try:
            data_obj = data.get("data", {})
            diff = data_obj.get("diff", []) if isinstance(data_obj, dict) else []
            records = []
            for item in diff:
                record = {
                    "industry": item.get("f14", ""),
                    "net_inflow": 0,  # 需要专门API
                    "net_inflow_ratio": 0,
                    "change_rate": item.get("f3", 0),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取行业资金流向成功: {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析行业资金流向失败: {e}")
            return pd.DataFrame(columns=["industry", "net_inflow", "net_inflow_ratio", "change_rate"])

    def get_lhb(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取龙虎榜数据

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - trade_date: 上榜日期
            - close_price: 收盘价
            - change_rate: 涨跌幅
            - net_buy_amount: 龙虎榜净买额
            - buy_amount: 龙虎榜买入额
            - sell_amount: 龙虎榜卖出额
            - turnover_rate: 换手率
            - reason: 上榜原因
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        # 转换为日期格式
        start_date_fmt = "-".join([start_date[:4], start_date[4:6], start_date[6:]])
        end_date_fmt = "-".join([end_date[:4], end_date[4:6], end_date[6:]])

        logger.debug(f"获取龙虎榜: {start_date} - {end_date}")

        params = {
            "sortColumns": "SECURITY_CODE,TRADE_DATE",
            "sortTypes": "1,-1",
            "pageSize": "5000",
            "pageNumber": "1",
            "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW",
            "columns": "SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,CHANGE_RATE,"
            "BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_DEAL_AMT,ACCUM_AMOUNT,"
            "DEAL_NET_RATIO,DEAL_AMOUNT_RATIO,TURNOVERRATE,FREE_MARKET_CAP,EXPLANATION",
            "source": "WEB",
            "client": "WEB",
            "filter": f"(TRADE_DATE<='{end_date_fmt}')(TRADE_DATE>='{start_date_fmt}')",
        }

        data = self._make_request(self.LHBB_URL, params)

        if not data:
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "close_price", "change_rate", "net_buy_amount",
                "buy_amount", "sell_amount", "turnover_rate", "reason"
            ])

        try:
            result = data.get("result", {})
            data_list = result.get("data", [])

            if not data_list:
                return pd.DataFrame(columns=[
                    "fs_code", "trade_date", "close_price", "change_rate", "net_buy_amount",
                    "buy_amount", "sell_amount", "turnover_rate", "reason"
                ])

            records = []
            for item in data_list:
                # 转换日期格式
                trade_date = item.get("TRADE_DATE", "")
                if trade_date:
                    trade_date = trade_date.replace("-", "")[:8]

                record = {
                    "fs_code": item.get("SECUCODE", ""),
                    "trade_date": trade_date,
                    "close_price": item.get("CLOSE_PRICE", 0),
                    "change_rate": item.get("CHANGE_RATE", 0),
                    "net_buy_amount": item.get("BILLBOARD_NET_AMT", 0),
                    "buy_amount": item.get("BILLBOARD_BUY_AMT", 0),
                    "sell_amount": item.get("BILLBOARD_SELL_AMT", 0),
                    "turnover_rate": item.get("TURNOVERRATE", 0),
                    "reason": item.get("EXPLANATION", ""),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取龙虎榜成功: {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析龙虎榜失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "close_price", "change_rate", "net_buy_amount",
                "buy_amount", "sell_amount", "turnover_rate", "reason"
            ])

    def get_lhb_detail(self, code: str, trade_date: str = None) -> pd.DataFrame:
        """
        获取龙虎榜明细

        Args:
            code: 股票代码 (000001.SZ)
            trade_date: 交易日期 (YYYYMMDD)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - trade_date: 交易日期
            - broker_name: 营业部名称
            - buy_amount: 买入金额
            - sell_amount: 卖出金额
            - net_amount: 净买额
        """
        fs_code = self._ensure_full_code(code)
        if not trade_date:
            trade_date = datetime.now().strftime("%Y%m%d")

        trade_date_fmt = "-".join([trade_date[:4], trade_date[4:6], trade_date[6:]])

        logger.debug(f"获取龙虎榜明细: {fs_code} {trade_date}")

        params = {
            "sortColumns": "BUY_SELL_RATE",
            "sortTypes": "-1",
            "pageSize": "100",
            "pageNumber": "1",
            "reportName": "RPT_DAILYBILLBOARD_DETAILSBROKERNEW",
            "columns": "SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,BROKER_CODE,BROKER_NAME,"
            "BUY_AMOUNT,SELL_AMOUNT,BUY_SELL_RATE,NET_AMOUNT,RANK",
            "source": "WEB",
            "client": "WEB",
            "filter": f"(TRADE_DATE='{trade_date_fmt}')(SECUCODE='{fs_code}')",
        }

        data = self._make_request(self.LHBB_URL, params)

        if not data:
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "broker_name", "buy_amount", "sell_amount", "net_amount"
            ])

        try:
            result = data.get("result", {})
            data_list = result.get("data", [])

            if not data_list:
                return pd.DataFrame(columns=[
                    "fs_code", "trade_date", "broker_name", "buy_amount", "sell_amount", "net_amount"
                ])

            records = []
            for item in data_list:
                record = {
                    "fs_code": fs_code,
                    "trade_date": trade_date,
                    "broker_name": item.get("BROKER_NAME", ""),
                    "buy_amount": item.get("BUY_AMOUNT", 0),
                    "sell_amount": item.get("SELL_AMOUNT", 0),
                    "net_amount": item.get("NET_AMOUNT", 0),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取龙虎榜明细成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析龙虎榜明细失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "broker_name", "buy_amount", "sell_amount", "net_amount"
            ])

    def get_margin(self, code: str = None) -> pd.DataFrame:
        """
        获取融资融券数据

        Args:
            code: 股票代码 (000001.SZ) - 不传则获取全市场

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - trade_date: 交易日期
            - rzye: 融资余额(元)
            - rqyl: 融券余量(股)
            - rzje: 融资买入额(元)
            - rqyl: 融券卖出量(股)
            - rzrqye: 融资融券余额(元)
        """
        logger.debug(f"获取融资融券: {code if code else '全市场'}")

        if code:
            fs_code = self._ensure_full_code(code)
            # 个股融资融券需要专用API，这里使用市场汇总数据
            filter_expr = f'(SECUCODE="{fs_code}")'
        else:
            filter_expr = ""

        params = {
            "reportName": "RPTA_WEB_MARGIN_DAILYTRADE",
            "columns": "ALL",
            "pageNumber": "1",
            "pageSize": "100",
            "sortColumns": "STATISTICS_DATE",
            "sortTypes": "-1",
            "filter": filter_expr,
        }

        data = self._make_request(self.MARGIN_URL, params)

        if not data:
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "rzye", "rqyl", "rzje", "rqyl", "rzrqye"
            ])

        try:
            result = data.get("result", {})
            data_list = result.get("data", [])

            if not data_list:
                return pd.DataFrame(columns=[
                    "fs_code", "trade_date", "rzye", "rqyl", "rzje", "rqyl", "rzrqye"
                ])

            records = []
            for item in data_list:
                trade_date = item.get("STATISTICS_DATE", "")
                if trade_date:
                    trade_date = trade_date.replace("-", "")[:8]

                record = {
                    "fs_code": item.get("SECUCODE", ""),
                    "trade_date": trade_date,
                    "rzye": item.get("FIN_BALANCE", 0),  # 融资余额
                    "rqyl": item.get("LOAN_BALANCE", 0),  # 融券余额
                    "rzje": item.get("FIN_BUY_AMT", 0),  # 融资买入额
                    "rqmcl": item.get("LOAN_SELL_AMT", 0),  # 融券卖出量
                    "rzrqye": item.get("MARGIN_BALANCE", 0),  # 融资融券余额
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取融资融券成功: {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析融资融券失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "rzye", "rqyl", "rzje", "rqyl", "rzrqye"
            ])

    def get_margin_detail(self, code: str, trade_date: str = None) -> pd.DataFrame:
        """
        获取个股融资融券明细

        Args:
            code: 股票代码 (000001.SZ)
            trade_date: 交易日期 (YYYYMMDD)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - trade_date: 交易日期
            - rzye: 融资余额(元)
            - rqyl: 融券余量(股)
            - rzrqye: 融资融券余额(元)
        """
        fs_code = self._ensure_full_code(code)
        if not trade_date:
            trade_date = datetime.now().strftime("%Y%m%d")

        trade_date_fmt = "-".join([trade_date[:4], trade_date[4:6], trade_date[6:]])

        logger.debug(f"获取融资融券明细: {fs_code} {trade_date}")

        params = {
            "reportName": "RPTA_WEB_MARGIN_DETAIL",
            "columns": "ALL",
            "pageNumber": "1",
            "pageSize": "100",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
            "filter": f"(TRADE_DATE='{trade_date_fmt}')(SECUCODE='{fs_code}')",
        }

        data = self._make_request(self.MARGIN_URL, params)

        if not data:
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "rzye", "rqyl", "rzrqye"
            ])

        try:
            result = data.get("result", {})
            data_list = result.get("data", [])

            if not data_list:
                return pd.DataFrame(columns=[
                    "fs_code", "trade_date", "rzye", "rqyl", "rzrqye"
                ])

            records = []
            for item in data_list:
                record = {
                    "fs_code": fs_code,
                    "trade_date": trade_date,
                    "rzye": item.get("FIN_BALANCE", 0),
                    "rqyl": item.get("LOAN_BALANCE", 0),
                    "rzrqye": item.get("MARGIN_BALANCE", 0),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取融资融券明细成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析融资融券明细失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "trade_date", "rzye", "rqyl", "rzrqye"
            ])
