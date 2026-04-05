# scripts/validate_sources.py
"""Phase 0: 源可用性验证。

逐个调用新浪/东财的候选端点，确认是否存活、返回格式是否正确。
输出验证报告，用于决定 Plan B 中每个数据类型的有效源清单。

Usage:
    python scripts/validate_sources.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime

import requests


def check_endpoint(name: str, url: str, params: dict | None = None, expect_keys: list[str] | None = None) -> dict:
    """Check a single endpoint and return validation result."""
    result = {"name": name, "url": url, "status": "unknown", "latency_ms": 0, "error": "", "sample_keys": []}
    start = time.monotonic()
    try:
        resp = requests.get(url, params=params, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        result["latency_ms"] = int((time.monotonic() - start) * 1000)
        result["http_status"] = resp.status_code

        if resp.status_code != 200:
            result["status"] = "FAIL"
            result["error"] = f"HTTP {resp.status_code}"
            return result

        try:
            data = resp.json()
            if isinstance(data, dict):
                result["sample_keys"] = list(data.keys())[:10]
            result["status"] = "OK"
        except json.JSONDecodeError:
            text = resp.text[:200]
            if "callback" in text or "jQuery" in text:
                result["status"] = "OK (JSONP)"
            elif "<html" in text.lower():
                result["status"] = "OK (HTML)"
            else:
                result["status"] = "OK (text)"

    except requests.Timeout:
        result["status"] = "FAIL"
        result["error"] = "timeout (10s)"
        result["latency_ms"] = 10000
    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)

    return result


ENDPOINTS = [
    {
        "name": "东财API: 概念板块列表",
        "url": "https://push2.eastmoney.com/api/qt/clist/get",
        "params": {"pn": "1", "pz": "20", "fs": "m:90+t:3+f:!50", "fields": "f2,f3,f12,f14,f62,f184"},
    },
    {
        "name": "新浪: 概念板块",
        "url": "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php",
        "params": {},
    },
    {
        "name": "东财API: 行业资金流",
        "url": "https://push2.eastmoney.com/api/qt/clist/get",
        "params": {"pn": "1", "pz": "20", "fs": "m:90+t:2", "fields": "f3,f12,f14,f62,f184"},
    },
    {
        "name": "新浪: 行业资金流",
        "url": "https://vip.stock.finance.sina.com.cn/moneyflow/",
        "params": {},
    },
    {
        "name": "东财API: 个股资金流",
        "url": "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
        "params": {"secid": "0.000001", "fields1": "f1,f2,f3", "fields2": "f51,f52,f53,f54,f55,f56,f57"},
    },
    {
        "name": "东财API: 业绩预告",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {"reportName": "RPT_PUBLIC_OP_NEWPREDICT", "pageSize": "5", "pageNumber": "1"},
    },
    {
        "name": "东财API: 分钟K线",
        "url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "params": {"secid": "0.000001", "klt": "5", "fqt": "0", "beg": "0", "end": "20500101"},
    },
    {
        "name": "新浪: 分钟K线",
        "url": "https://quotes.sina.cn/cn/api/jsonp.php/var/InnerExtensionService.getMinKLine",
        "params": {"symbol": "sz000001", "scale": "5", "datalen": "10"},
    },
    {
        "name": "东财API: 涨跌统计",
        "url": "https://push2.eastmoney.com/api/qt/ulist.np/get",
        "params": {"fltt": "2", "fields": "f104,f105,f106"},
    },
    {
        "name": "东财API: 融资融券汇总",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {"reportName": "RPTA_MUTUAL_MARKETSTAT", "pageSize": "5", "pageNumber": "1"},
    },
]


def main():
    print(f"=== 源可用性验证报告 ===")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"检查 {len(ENDPOINTS)} 个端点\n")

    results = []
    for ep in ENDPOINTS:
        r = check_endpoint(ep["name"], ep["url"], ep.get("params"))
        results.append(r)
        status_icon = "OK" if r["status"].startswith("OK") else "FAIL"
        print(f"[{status_icon}] {r['name']}")
        print(f"   状态: {r['status']}  延迟: {r['latency_ms']}ms")
        if r["error"]:
            print(f"   错误: {r['error']}")
        print()

    ok_count = sum(1 for r in results if r["status"].startswith("OK"))
    fail_count = len(results) - ok_count
    print(f"--- 汇总: {ok_count} 可用, {fail_count} 不可用 ---")

    if fail_count > 0:
        print("\n不可用的端点需要从 smart_router 配置中移除或替换。")
        sys.exit(1)


if __name__ == "__main__":
    main()
