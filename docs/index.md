# finshare

<div align="center">
  <h3>专业的金融数据获取工具库</h3>
  <p>🎉 完全免费 | 🚀 简单易用 | 📊 多数据源</p>
  <p>
    <a href="https://github.com/finvfamily/finshare">
      <img src="https://img.shields.io/github/stars/finvfamily/finshare" alt="Stars"/>
    </a>
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"/>
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"/>
  </p>
</div>

---

## 简介

finshare 是一个专业的金融数据获取 Python 库，支持从多个数据源获取股票、ETF、LOF 等金融产品的历史数据、实时行情、财务数据、特色数据等。

**完全免费**：无需 API Key，无调用次数限制

**主要特性**：
- 📊 多数据源支持（东方财富、腾讯、新浪、通达信、BaoStock）
- 🔄 自动故障切换，数据源失败时自动切换备用源
- ⚡ 高性能获取，支持异步批量获取
- 💾 内置缓存机制，减少重复请求
- 🔧 简单易用的 API 设计

---

## 安装

```bash
pip install finshare
```

---

## 快速开始

```python
import finshare as fs

# 获取历史K线数据
df = fs.get_historical_data('000001.SZ', start='2024-01-01', end='2024-01-31')
print(df.head())

# 获取实时快照
snapshot = fs.get_snapshot_data('000001.SZ')
print(f"最新价: {snapshot.last_price}")
```

---

## 数据类型

### 1. K线历史数据

```python
import finshare as fs

# 获取日线数据
df = fs.get_historical_data(
    code='000001.SZ',      # 股票代码
    start='2024-01-01',   # 开始日期
    end='2024-12-31',     # 结束日期
    adjust='qfq'           # 复权类型: qfq(前复权) / hfq(后复权) / None(不复权)
)

print(df.head())
#         code  trade_date  open_price  high_price  low_price  close_price  volume      amount
# 0  000001.SZ  2024-01-02        7.83        7.95       7.78         7.90  79011200  621889760.0
```

### 2. 实时快照

```python
import finshare as fs

# 获取单只股票快照
snapshot = fs.get_snapshot_data('000001.SZ')
print(f"代码: {snapshot.code}")
print(f"最新价: {snapshot.last_price}")
print(f"涨跌额: {snapshot.change}")
print(f"涨跌幅: {snapshot.change_pct}%")
print(f"成交量: {snapshot.volume}")
print(f"成交额: {snapshot.amount}")

# 批量获取快照（更高效）
snapshots = fs.get_batch_snapshots(['000001.SZ', '600519.SH', '510300'])
for code, data in snapshots.items():
    print(f"{code}: {data.last_price}")
```

### 3. 财务数据

```python
import finshare as fs

# 利润表
df = fs.get_income('000001.SZ')
print(df.head())

# 资产负债表
df = fs.get_balance('000001.SZ')
print(df.head())

# 现金流量表
df = fs.get_cashflow('000001.SZ')
print(df.head())

# 财务指标
df = fs.get_financial_indicator('000001.SZ')
print(df.head())
#    fs_code report_date    eps   roe  gross_margin  debt_to_assets
# 0  000001.SZ   20240630  0.85  10.2          25.3           93.5
```

### 4. 特色数据

```python
import finshare as fs

# 资金流向
df = fs.get_money_flow('000001.SZ')
print(df.head())
#    fs_code trade_date  net_inflow_main  net_inflow_main_ratio
# 0  000001.SZ   20240927      -123456789.0                -2.35

# 行业资金流向
df = fs.get_money_flow_industry()
print(df.head())

# 龙虎榜
df = fs.get_lhb()
print(df.head())

# 融资融券
df = fs.get_margin('000001.SZ')
print(df.head())
```

### 5. 异步获取

```python
import asyncio
import finshare as fs

async def main():
    # 获取异步管理器
    async_mgr = fs.get_async_manager(max_workers=10)

    # 批量异步获取快照
    codes = ['000001.SZ', '600519.SH', '000002.SZ']
    df = await async_mgr.get_batch_snapshot(codes)
    print(df)

    async_mgr.close()

asyncio.run(main())
```

### 6. 缓存使用

```python
import finshare as fs

# 使用缓存装饰器
@fs.cached(ttl=300, key_prefix="stock_")
def get_stock_price(code):
    # 模拟API调用
    return fs.get_snapshot_data(code)

# 第一次调用
result1 = get_stock_price('000001.SZ')

# 第二次调用（命中缓存）
result2 = get_stock_price('000001.SZ')

# 手动清除缓存
get_stock_price.clear_cache()
```

---

## 代码说明

### 支持的股票代码格式

finshare 支持多种股票代码格式：

```python
# 以下格式均可使用
'000001.SZ'   # 标准格式
'000001'      # 纯数字（自动识别市场）
'SZ000001'    # SZ前缀
'sh600519'    # 小写也可以
```

### 支持的市场

| 市场 | 代码后缀 | 示例 |
|------|----------|------|
| 深圳 | .SZ | 000001.SZ |
| 上海 | .SH | 600519.SH |
| 北京 | .BJ | 430001.BJ |

---

## API 参考

### 核心函数

| 函数 | 说明 |
|------|------|
| `fs.get_historical_data()` | 获取K线历史数据 |
| `fs.get_snapshot_data()` | 获取实时快照 |
| `fs.get_batch_snapshots()` | 批量获取快照 |

### 财务数据

| 函数 | 说明 |
|------|------|
| `fs.get_income()` | 利润表 |
| `fs.get_balance()` | 资产负债表 |
| `fs.get_cashflow()` | 现金流量表 |
| `fs.get_financial_indicator()` | 财务指标 |

### 特色数据

| 函数 | 说明 |
|------|------|
| `fs.get_money_flow()` | 资金流向 |
| `fs.get_money_flow_industry()` | 行业资金流向 |
| `fs.get_lhb()` | 龙虎榜 |
| `fs.get_margin()` | 融资融券 |

### 高级功能

| 函数 | 说明 |
|------|------|
| `fs.get_async_manager()` | 异步数据管理器 |
| `fs.MemoryCache()` | 内存缓存 |
| `fs.cached()` | 缓存装饰器 |
| `fs.CircuitBreaker()` | 熔断器 |
| `fs.SmartRouter()` | 智能路由 |

---

## 数据字段说明

### K线数据 (DataFrame)

| 字段 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码 |
| trade_date | str | 交易日期 |
| open_price | float | 开盘价 |
| high_price | float | 最高价 |
| low_price | float | 最低价 |
| close_price | float | 收盘价 |
| volume | float | 成交量(手) |
| amount | float | 成交额(元) |

### 快照数据 (SnapshotData)

| 字段 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码 |
| last_price | float | 最新价 |
| change | float | 涨跌额 |
| change_pct | float | 涨跌幅 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| prev_close | float | 昨收价 |
| volume | float | 成交量 |
| amount | float | 成交额 |

---

## 常见问题

### Q: 需要 API Key 吗？
A: 不需要，finshare 完全免费使用。

### Q: 有调用次数限制吗？
A: 没有硬性限制，但建议合理使用，设置适当的请求间隔。

### Q: 数据从哪里获取？
A: finshare 从多个公开数据源获取（东方财富、腾讯、新浪等），不存储数据。

### Q: 支持哪些 Python 版本？
A: 支持 Python 3.8 及以上版本。

---

## 相关链接

- **GitHub**: https://github.com/finvfamily/finshare
- **PyPI**: https://pypi.org/project/finshare
- **Discord**: https://discord.gg/XT5f8ZGB
- **官网**: https://meepoquant.com

---

<div align="center">
  <p>🎉 如果这个项目对你有帮助，请给我们一个 Star！</p>
  <p>由 <a href="https://meepoquant.com">米波量化</a> 团队开发维护</p>
</div>
