import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestPlaywrightEastMoneySource:
    def test_source_name(self):
        from finshare.sources.playwright_source import PlaywrightEastMoneySource
        source = PlaywrightEastMoneySource()
        assert source.source_name == "playwright_eastmoney"

    def test_source_tier(self):
        from finshare.sources.playwright_source import PlaywrightEastMoneySource
        source = PlaywrightEastMoneySource()
        assert source.source_tier == "scraper"

    def test_is_available_false_when_playwright_missing(self):
        from finshare.sources.playwright_source import PlaywrightEastMoneySource
        source = PlaywrightEastMoneySource()
        with patch("finshare.sources.playwright_source.pw_is_available", return_value=False):
            assert source.is_available() is False

    def test_get_concept_list_returns_dataframe(self):
        from finshare.sources.playwright_source import PlaywrightEastMoneySource
        source = PlaywrightEastMoneySource()
        mock_data = [
            {"board_code": "BK0493", "board_name": "新能源", "change_pct": "2.35", "net_inflow": "1000000", "net_inflow_ratio": "5.2"},
            {"board_code": "BK0655", "board_name": "芯片", "change_pct": "-1.20", "net_inflow": "-500000", "net_inflow_ratio": "-2.1"},
        ]
        with patch("finshare.sources.playwright_source.pw_is_available", return_value=True):
            with patch.object(source, "_concept_list_scraper") as mock_scraper:
                mock_scraper.fetch.return_value = mock_data
                df = source.get_concept_list()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["board_code", "board_name", "change_pct", "net_inflow", "net_inflow_ratio"]
        assert df["change_pct"].dtype == float
        assert df["net_inflow"].dtype == float

    def test_get_concept_list_returns_empty_when_unavailable(self):
        from finshare.sources.playwright_source import PlaywrightEastMoneySource
        source = PlaywrightEastMoneySource()
        with patch("finshare.sources.playwright_source.pw_is_available", return_value=False):
            df = source.get_concept_list()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestPlaywrightSinaSource:
    def test_source_name(self):
        from finshare.sources.playwright_source import PlaywrightSinaSource
        source = PlaywrightSinaSource()
        assert source.source_name == "playwright_sina"

    def test_source_tier(self):
        from finshare.sources.playwright_source import PlaywrightSinaSource
        source = PlaywrightSinaSource()
        assert source.source_tier == "scraper"


class TestToFloat:
    def test_normal_number(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("123.45") == 123.45

    def test_with_percent(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("2.35%") == 2.35

    def test_with_comma(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("1,234,567") == 1234567.0

    def test_dash_returns_default(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("-") == 0.0
        assert _to_float("--") == 0.0

    def test_empty_returns_default(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("") == 0.0

    def test_invalid_returns_default(self):
        from finshare.sources.playwright_source import _to_float
        assert _to_float("abc") == 0.0
