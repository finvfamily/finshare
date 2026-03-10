# finshare

<div align="center">
  <h3>专业的金融数据获取工具库</h3>
  <p>A Professional Financial Data Fetching Toolkit for Python</p>

  <p>
    <a href="https://meepoquant.com">官网</a> •
    <a href="https://github.com/finvfamily/finshare">GitHub</a> •
    <a href="https://discord.gg/XT5f8ZGB">Discord</a> •
    <a href="https://github.com/finvfamily/finshare/issues">问题反馈</a>
  </p>

  <p>
    <img src="https://img.shields.io/github/stars/finvfamily/finshare" alt="Stars"/>
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"/>
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"/>
  </p>
</div>

---

## 🚀 快速开始

```python
from finshare import get_data_manager

# 获取数据管理器
manager = get_data_manager()

# 获取 K线数据（只需传入股票代码，无需市场后缀）
data = manager.get_historical_data(
    code='000001',
    start='2024-01-01',
    end='2024-01-31',
    adjust='qfq'  # 前复权
)
print(data.head())

# 获取实时快照
snapshot = manager.get_snapshot_data('000001')
print(f"最新价: {snapshot.last_price}")
print(f"涨跌幅: {(snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100:.2f}%")
```

## ✨ 核心特性

- 📊 **多数据源支持** - 东方财富、腾讯、新浪、通达信、BaoStock
- 🔄 **自动故障切换** - 数据源失败时自动切换到备用源
- 📈 **统一数据格式** - 所有数据源返回统一的 DataFrame 格式
- ⚡ **高性能获取** - 优化的数据获取和解析性能
- 🔧 **简单易用** - 简洁的 API 设计，开箱即用
- 🤖 **AI 驱动开发** - 完全由 Claude AI 实现，代码质量有保障

## 📦 安装

```bash
pip install finshare
```

**注意**: 包名为 `finshare`，但导入时使用 `finshare`：

```python
import finshare
from finshare import get_data_manager
```

## 📚 支持的数据源

| 数据源 | K线数据 | 实时快照 | 复权数据 |
|--------|---------|----------|----------|
| 东方财富 | ✅ | ✅ | ✅ |
| 腾讯财经 | ✅ | ✅ | ✅ |
| 新浪财经 | ❌ | ✅ | ❌ |
| 通达信 | ✅ | ✅ | ✅ |
| BaoStock | ✅ | ✅ | ✅ |

## 💡 使用示例

### 基础用法

```python
from finshare import get_data_manager, logger

manager = get_data_manager()

# 获取日线数据（只需传入6位股票代码）
data = manager.get_historical_data(
    code='000001',  # 平安银行
    start='2024-01-01',
    end='2024-01-31',
    adjust='qfq'  # 前复权
)

if data is not None and len(data) > 0:
    logger.info(f"成功获取 {len(data)} 条数据")
    logger.info(f"开盘价: {data['open_price'].iloc[0]:.2f}")
    logger.info(f"收盘价: {data['close_price'].iloc[-1]:.2f}")
    logger.info(f"最高价: {data['high_price'].max():.2f}")
    logger.info(f"最低价: {data['low_price'].min():.2f}")

# 获取实时快照
snapshot = manager.get_snapshot_data('000001')
if snapshot:
    logger.info(f"股票代码: {snapshot.code}")
    logger.info(f"最新价格: {snapshot.last_price}")
    logger.info(f"成交量: {snapshot.volume}")
    logger.info(f"成交额: {snapshot.amount}")
    if snapshot.prev_close:
        change_percent = (snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100
        logger.info(f"涨跌幅: {change_percent:.2f}%")
```

### 批量获取

```python
from finshare import get_data_manager, logger

manager = get_data_manager()

# 批量获取多只股票（使用6位代码）
symbols = ['000001', '000002', '600000', '600036']

results = {}
for symbol in symbols:
    try:
        logger.info(f"正在获取 {symbol}...")
        data = manager.get_historical_data(
            code=symbol,
            start='2024-01-01',
            end='2024-01-31'
        )

        if data is not None and len(data) > 0:
            results[symbol] = data
            logger.info(f"✓ {symbol}: {len(data)} 条数据")
        else:
            logger.warning(f"✗ {symbol}: 未获取到数据")
    except Exception as e:
        logger.error(f"✗ {symbol}: {e}")

# 数据分析示例
if results:
    logger.info("\n数据分析:")
    for symbol, data in results.items():
        change = (data['close_price'].iloc[-1] - data['close_price'].iloc[0]) / data['close_price'].iloc[0] * 100
        logger.info(f"  {symbol}: 涨跌幅 {change:+.2f}%")
```

### 批量获取实时快照

```python
from finshare import get_data_manager, logger

manager = get_data_manager()

# 支持股票、ETF、LOF 等多种类型
symbols = [
    "000001",  # 股票：平安银行
    "600519",  # 股票：贵州茅台
    "510300",  # ETF：沪深300ETF
    "159915",  # ETF：创业板ETF
    "163402",  # LOF：兴全趋势
]

# 使用批量接口获取快照（更高效）
results = manager.get_batch_snapshots(symbols)

# 展示实时行情
if results:
    logger.info(f"成功获取 {len(results)} 只股票的快照")
    for symbol, snapshot in results.items():
        change_percent = 0.0
        if snapshot.prev_close and snapshot.prev_close > 0:
            change_percent = (snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100
        logger.info(f"{symbol}: {snapshot.last_price:.2f} ({change_percent:+.2f}%)")
```
```

### 使用特定数据源

```python
from finshare import EastMoneyDataSource, TencentDataSource

# 使用东方财富
eastmoney = EastMoneyDataSource()
data = eastmoney.get_historical_data('000001', start='2024-01-01')

# 使用腾讯财经
tencent = TencentDataSource()
data = tencent.get_historical_data('000001', start='2024-01-01')
```

## 🌟 为什么选择 finshare？

finshare 是 [米波量化平台](https://meepoquant.com) 的数据层，经过生产环境验证，稳定可靠。

### 完整的量化交易解决方案

如果你需要更强大的功能，可以使用**完全免费**的米波量化平台：

| 功能 | finshare | 米波量化 |
|------|-----------|----------|
| 数据获取 | ✅ 开源免费 | ✅ 完全免费 |
| 策略回测 | ❌ | ✅ 完全免费 |
| 参数优化 | ❌ | ✅ 完全免费 |
| 30+ 内置策略 | ❌ | ✅ 完全免费 |
| 策略市场 | ❌ | ✅ 完全免费 |
| 实盘监控 | ❌ | ✅ 完全免费 |

**🎉 米波量化所有功能永久免费，无次数限制，无功能阉割**

👉 [立即体验米波量化](https://meepoquant.com?from=github)

## 📖 文档

- [快速开始](https://github.com/finvfamily/finshare#-快速开始)
- [使用示例](https://github.com/finvfamily/finshare#-使用示例)
- [数据源说明](https://github.com/finvfamily/finshare#-支持的数据源)
- [示例代码](https://github.com/finvfamily/finshare/tree/main/examples)

## 🤝 贡献

欢迎贡献代码！查看 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🔗 相关链接

- **官方网站**: https://meepoquant.com
- **GitHub**: https://github.com/finvfamily/finshare
- **Discord**: https://discord.gg/XT5f8ZGB
- **PyPI**: https://pypi.org/project/finshare
- **问题反馈**: https://github.com/finvfamily/finshare/issues

---

<div align="center">
  <p>
    <strong>由 <a href="https://meepoquant.com">米波量化</a> 团队开发和维护</strong>
  </p>
  <p>
    🤖 本项目完全由 AI (Claude) 实现，展示了 AI 在软件工程领域的强大能力
  </p>
  <p>
    ⭐ 如果这个项目对你有帮助，请给我们一个 Star！
  </p>
  <p>
    💡 需要完整的量化交易平台？访问 <a href="https://meepoquant.com">米波量化</a> - 完全免费，无限使用
  </p>
  <p>
    🚀 <strong>开源计划</strong>：米波量化回测框架计划于 2026 Q2 开源（MIT License）
  </p>
</div>

