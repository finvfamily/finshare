# finshare 多数据源容灾修复

## 目标

修复所有挂掉/截断的 API，给证券列表等数据类型加备份数据源，走 SmartRouter 自动切换。

## 第一批：修分页 bug

### 1.1 龙虎榜 `get_lhb()`
- 文件：`stock/feature/client.py`
- 问题：`pageSize=5000` 但 API 限 500/页，只取到 1/3 数据
- 修复：pageSize 改 500，加分页循环 + total 判断

### 1.2 融资融券 `get_margin()`
- 文件：`stock/feature/client.py`
- 问题：pageSize=100 无分页，3269 条只取 100 条
- 修复：加分页循环 + total 判断

## 第二批：修死掉的 API

### 2.1 PE/PB 估值 `get_index_pe()` / `get_index_pb()` / `get_market_pb()`
- 文件：`stock/valuation/client.py`
- 问题：legulegu.com 全线 404
- 修复：改用东方财富 datacenter 历史 PE/PB 接口
  - URL: `https://datacenter-web.eastmoney.com/api/data/v1/get`
  - 参数: `reportName=RPT_VALUEANALYSIS_DET` (指数估值分析)
  - 返回历史 PE/PB 序列

### 2.2 全球指数 `get_global_index_daily()`
- 文件：`stock/valuation/client.py`
- 问题：GLOBAL_INDEX_MAP secid 映射错误（`100.HSI` 返回 rc=102）
- 修复：对标 akshare 修正 secid 映射

### 2.3 基金列表 `get_fund_list()`
- 文件：`sources/fund_source.py`
- 问题：`fund.eastmoney.com/data/fund_rank_list` 返回 404
- 修复：换 `fund.eastmoney.com/js/fundcode_search.js` 或 datacenter API

### 2.4 基金信息 `get_fund_info()`
- 文件：`sources/fund_source.py`
- 问题：HTML 解析失败，只返回 code
- 修复：改用 `fund.eastmoney.com/pingzhongdata/{code}.js` 的 JSON 字段

### 2.5 分红数据 `get_dividend()`
- 文件：`stock/financial/client.py`
- 问题：硬编码返回空 DataFrame
- 修复：接入 `datacenter-web.eastmoney.com` 分红接口
  - `reportName=RPT_SHAREBONUS_DET`

## 第三批：加备份数据源

### 3.1 BaoStock 加 `get_stock_list()`
- 文件：`sources/baostock_source.py`
- 方法：调 `bs.query_stock_basic()` 获取全量 A 股列表
- 返回格式：与 EastMoney `get_stock_list()` 一致的 `List[dict]`

### 3.2 BaoStock 加 `get_industry_list()`
- 文件：`sources/baostock_source.py`
- 方法：调 `bs.query_stock_industry()` 获取行业分类

## 第四批：SmartRouter 扩展

### 4.1 新增 DataType
在 `sources/resilience/smart_router.py` 中添加：
```python
STOCK_LIST = "stock_list"
VALUATION = "valuation"
INDUSTRY = "industry"
DIVIDEND = "dividend"
```

### 4.2 容灾链配置
```python
DataType.STOCK_LIST:   [EastMoney(1), BaoStock(2)]
DataType.VALUATION:    [EastMoney(1)]
DataType.INDUSTRY:     [EastMoney(1), BaoStock(2)]
DataType.LHB:          [EastMoney(1)]
DataType.MARGIN:       [EastMoney(1)]
DataType.DIVIDEND:     [EastMoney(1)]
DataType.GLOBAL_INDEX: [EastMoney(1)]
```

### 4.3 DataSourceManager 加对应方法
在 `sources/manager.py` 中加：
- `get_stock_list()` — 走 SmartRouter，EastMoney 失败自动切 BaoStock
- `get_industry_list()` — 同理

## Cooldown 隔离

当前问题：EastMoney clist 端点失败会把整个 "eastmoney" 源 cooldown，连带封锁正常的 kline/snapshot 端点。

修复：按端点分组 cooldown，不是按源分组。
- `eastmoney_clist` — push2 列表接口
- `eastmoney_kline` — push2his K 线接口
- `eastmoney_datacenter` — datacenter 接口
- `eastmoney_snapshot` — push2 快照接口
