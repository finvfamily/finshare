"""Playwright-based data sources, registered as scraper-tier in smart_router.

These wrap the generic table scrapers to provide the same method interface
as EastMoneyDataSource / SinaDataSource, but using browser automation.
They are ONLY used when all api-tier sources are unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from finshare.sources.playwright import is_available as pw_is_available
from finshare.sources.playwright.eastmoney_table_scraper import EastMoneyTableScraper
from finshare.sources.playwright.sina_table_scraper import SinaFinanceTableScraper

logger = logging.getLogger(__name__)


def _to_float(val: str, default: float = 0.0) -> float:
    """Convert string to float, stripping %, commas, etc."""
    if not val or val == "-" or val == "--":
        return default
    try:
        return float(val.replace(",", "").replace("%", "").replace("亿", "").replace("万", ""))
    except (ValueError, TypeError):
        return default


# -- Scraper configurations for EastMoney pages --

_CONCEPT_LIST_CONFIG = dict(
    url="https://quote.eastmoney.com/center/boardlist.html#concept_board",
    column_map={1: "board_code", 2: "board_name", 3: "change_pct", 8: "net_inflow", 9: "net_inflow_ratio"},
    next_selector="a.next",
)

_CONCEPT_MONEY_FLOW_CONFIG = dict(
    url="https://data.eastmoney.com/bkzj/gn.html",
    column_map={1: "concept", 3: "net_inflow", 4: "net_inflow_ratio", 2: "change_rate"},
    next_selector="a.next",
)


class PlaywrightEastMoneySource:
    """东财 Playwright 数据源（scraper 层）。"""

    source_name = "playwright_eastmoney"
    source_tier = "scraper"

    def __init__(self):
        self._concept_list_scraper = EastMoneyTableScraper(**_CONCEPT_LIST_CONFIG)
        self._concept_money_flow_scraper = EastMoneyTableScraper(**_CONCEPT_MONEY_FLOW_CONFIG)

    def is_available(self) -> bool:
        return pw_is_available()

    def get_concept_list(self) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        raw = self._concept_list_scraper.fetch(max_pages=20)
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["change_pct", "net_inflow", "net_inflow_ratio"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df

    def get_concept_constituents(self, concept_name: str, board_code: str = "") -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        url = f"https://quote.eastmoney.com/center/boardlist.html#boards2-BK{board_code}"
        scraper = EastMoneyTableScraper(
            url=url,
            column_map={1: "fs_code", 2: "name"},
            next_selector="a.next",
        )
        raw = scraper.fetch(max_pages=10)
        if not raw:
            return pd.DataFrame()
        return pd.DataFrame(raw)

    def get_concept_money_flow(self) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        raw = self._concept_money_flow_scraper.fetch(max_pages=20)
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["net_inflow", "net_inflow_ratio", "change_rate"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df

    def get_money_flow_industry(self) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = EastMoneyTableScraper(
            url="https://data.eastmoney.com/bkzj/hy.html",
            column_map={1: "industry", 3: "net_inflow", 4: "net_inflow_ratio", 2: "change_rate"},
            next_selector="a.next",
        )
        raw = scraper.fetch(max_pages=5)
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["net_inflow", "net_inflow_ratio", "change_rate"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df

    def get_money_flow_stock(self, code: str) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = EastMoneyTableScraper(
            url=f"https://data.eastmoney.com/zjlx/{code}.html",
            column_map={0: "trade_time", 1: "main_inflow", 2: "main_outflow", 3: "main_net",
                        4: "retail_inflow", 5: "retail_outflow", 6: "retail_net"},
        )
        raw = scraper.fetch()
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["main_inflow", "main_outflow", "main_net", "retail_inflow", "retail_outflow", "retail_net"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df

    def get_earnings_calendar(self, date: str) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = EastMoneyTableScraper(
            url=f"https://data.eastmoney.com/bbsj/202603.html",
            column_map={0: "code", 1: "name", 4: "report_date", 5: "report_type"},
            next_selector="a.next",
        )
        raw = scraper.fetch(max_pages=10)
        if not raw:
            return pd.DataFrame()
        return pd.DataFrame(raw)

    def get_earnings_preannouncement(self, code: str) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = EastMoneyTableScraper(
            url=f"https://data.eastmoney.com/bbsj/stock{code}.html",
            column_map={0: "report_period", 1: "pre_type", 2: "pre_profit_range", 3: "announce_date"},
        )
        raw = scraper.fetch()
        if not raw:
            return pd.DataFrame()
        return pd.DataFrame(raw)

    def get_market_overview(self) -> pd.DataFrame:
        # Market overview needs special aggregation — detailed implementation in Plan B
        return pd.DataFrame()


class PlaywrightSinaSource:
    """新浪 Playwright 数据源（scraper 层）。"""

    source_name = "playwright_sina"
    source_tier = "scraper"

    def __init__(self):
        pass

    def is_available(self) -> bool:
        return pw_is_available()

    def get_concept_list(self) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = SinaFinanceTableScraper(
            url="https://finance.sina.com.cn/stock/sl/",
            column_map={0: "board_name", 1: "change_pct", 2: "net_inflow"},
        )
        raw = scraper.fetch()
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["change_pct", "net_inflow"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df

    def get_money_flow_industry(self) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()
        scraper = SinaFinanceTableScraper(
            url="https://vip.stock.finance.sina.com.cn/moneyflow/",
            column_map={0: "industry", 1: "net_inflow", 2: "net_inflow_ratio", 3: "change_rate"},
        )
        raw = scraper.fetch()
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw)
        for col in ["net_inflow", "net_inflow_ratio", "change_rate"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_float)
        return df
