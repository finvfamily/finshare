"""
Tests for SmartRouter Source Tier Support (Task 1).

Tests cover:
- SourceTier enum values
- SourcePreference tier field (default and explicit)
- get_tiered_sources() method behaviour
"""
import pytest
from finshare.sources.resilience.smart_router import (
    SmartRouter,
    SourceTier,
    SourceType,
    DataType,
    SourcePreference,
)


class TestSourceTier:
    def test_source_tier_enum_values(self):
        assert SourceTier.API.value == "api"
        assert SourceTier.SCRAPER.value == "scraper"

    def test_source_preference_has_tier(self):
        pref = SourcePreference(
            source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API
        )
        assert pref.tier == SourceTier.API

    def test_source_preference_default_tier_is_api(self):
        pref = SourcePreference(
            source=SourceType.EASTMONEY, priority=1, timeout=10.0
        )
        assert pref.tier == SourceTier.API


class TestTieredRouting:
    def setup_method(self):
        self.router = SmartRouter()

    def test_get_tiered_sources_returns_api_first(self):
        prefs = [
            SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
            SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
            SourcePreference(source=SourceType.EASTMONEY, priority=3, timeout=30.0, tier=SourceTier.SCRAPER),
        ]
        self.router.preferences[DataType.MONEY_FLOW] = prefs

        api_sources, scraper_sources = self.router.get_tiered_sources(DataType.MONEY_FLOW)
        assert len(api_sources) == 2
        assert len(scraper_sources) == 1
        assert api_sources[0].source == SourceType.EASTMONEY
        assert api_sources[1].source == SourceType.SINA
        assert scraper_sources[0].tier == SourceTier.SCRAPER

    def test_get_tiered_sources_skips_unhealthy_sources(self):
        prefs = [
            SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
            SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
        ]
        self.router.preferences[DataType.MONEY_FLOW] = prefs
        self.router.update_source_health(SourceType.EASTMONEY, is_healthy=False, error_msg="timeout")

        api_sources, scraper_sources = self.router.get_tiered_sources(DataType.MONEY_FLOW)
        assert len(api_sources) == 1
        assert api_sources[0].source == SourceType.SINA

    def test_get_tiered_sources_skips_disabled(self):
        prefs = [
            SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API, enabled=False),
            SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
        ]
        self.router.preferences[DataType.MONEY_FLOW] = prefs

        api_sources, _ = self.router.get_tiered_sources(DataType.MONEY_FLOW)
        assert len(api_sources) == 1
        assert api_sources[0].source == SourceType.SINA


class TestNewDataTypes:
    def test_concept_list_data_type(self):
        assert DataType.CONCEPT_LIST.value == "concept_list"

    def test_concept_constituents_data_type(self):
        assert DataType.CONCEPT_CONSTITUENTS.value == "concept_constituents"

    def test_concept_money_flow_data_type(self):
        assert DataType.CONCEPT_MONEY_FLOW.value == "concept_money_flow"

    def test_money_flow_stock_data_type(self):
        assert DataType.MONEY_FLOW_STOCK.value == "money_flow_stock"

    def test_earnings_calendar_data_type(self):
        assert DataType.EARNINGS_CALENDAR.value == "earnings_calendar"

    def test_earnings_preannounce_data_type(self):
        assert DataType.EARNINGS_PREANNOUNCE.value == "earnings_preannounce"

    def test_market_overview_data_type(self):
        assert DataType.MARKET_OVERVIEW.value == "market_overview"

    def test_margin_summary_data_type(self):
        assert DataType.MARGIN_SUMMARY.value == "margin_summary"


class TestNewSourceTypes:
    def test_playwright_eastmoney_source_type(self):
        assert SourceType.PLAYWRIGHT_EASTMONEY.value == "playwright_eastmoney"

    def test_playwright_sina_source_type(self):
        assert SourceType.PLAYWRIGHT_SINA.value == "playwright_sina"


class TestDefaultPreferencesForNewDataTypes:
    def setup_method(self):
        self.router = SmartRouter()

    def _assert_has_api_preferences(self, data_type: DataType):
        api_sources, scraper_sources = self.router.get_tiered_sources(data_type)
        assert len(api_sources) >= 1, f"Expected at least one API source for {data_type}"
        for src in api_sources:
            assert src.tier == SourceTier.API

    def test_concept_list_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.CONCEPT_LIST)

    def test_concept_constituents_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.CONCEPT_CONSTITUENTS)

    def test_concept_money_flow_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.CONCEPT_MONEY_FLOW)

    def test_money_flow_stock_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.MONEY_FLOW_STOCK)

    def test_earnings_calendar_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.EARNINGS_CALENDAR)

    def test_earnings_preannounce_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.EARNINGS_PREANNOUNCE)

    def test_market_overview_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.MARKET_OVERVIEW)

    def test_margin_summary_has_default_preferences(self):
        self._assert_has_api_preferences(DataType.MARGIN_SUMMARY)


class TestGetTieredSourcesEdgeCases:
    def setup_method(self):
        self.router = SmartRouter()

    def test_get_tiered_sources_unknown_data_type_returns_empty(self):
        # DataType.CONCEPT_LIST won't be in preferences if we use a fresh SmartRouter
        # with custom empty preferences
        router = SmartRouter(preferences={})
        api_sources, scraper_sources = router.get_tiered_sources(DataType.SNAPSHOT)
        assert api_sources == []
        assert scraper_sources == []

    def test_get_tiered_sources_respects_priority_order(self):
        prefs = [
            SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
            SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        ]
        self.router.preferences[DataType.DAILY] = prefs

        api_sources, _ = self.router.get_tiered_sources(DataType.DAILY)
        assert len(api_sources) == 2
        # priority=1 (EASTMONEY) should come first
        assert api_sources[0].source == SourceType.EASTMONEY
        assert api_sources[1].source == SourceType.SINA

    def test_get_tiered_sources_all_disabled_returns_empty(self):
        prefs = [
            SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, enabled=False),
        ]
        self.router.preferences[DataType.MONEY_FLOW] = prefs

        api_sources, scraper_sources = self.router.get_tiered_sources(DataType.MONEY_FLOW)
        assert api_sources == []
        assert scraper_sources == []

    def test_get_tiered_sources_scraper_tier_also_skips_unhealthy(self):
        prefs = [
            SourcePreference(
                source=SourceType.PLAYWRIGHT_EASTMONEY, priority=1, timeout=30.0, tier=SourceTier.SCRAPER
            ),
        ]
        self.router.preferences[DataType.MONEY_FLOW] = prefs
        self.router.update_source_health(SourceType.PLAYWRIGHT_EASTMONEY, is_healthy=False, error_msg="crashed")

        _, scraper_sources = self.router.get_tiered_sources(DataType.MONEY_FLOW)
        assert scraper_sources == []
