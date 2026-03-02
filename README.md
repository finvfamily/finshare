# finshare

<div align="center">
  <h3>专业的金融数据获取工具库</h3>
  <p>A Professional Financial Data Fetching Toolkit for Python</p>

  <p>
    <a href="https://meepoquant.com">官网</a> •
    <a href="https://github.com/finvfamily/finshare">GitHub</a> •
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
data = manager.get_kline('000001', start='2024-01-01', end='2024-01-31')
print(data.head())

# 获取实时快照
snapshot = manager.get_snapshot('000001')
print(f"最新价: {snapshot.last_price}")
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
from finshare import get_data_manager

manager = get_data_manager()

# 获取日线数据（只需传入6位股票代码）
data = manager.get_kline(
    code='000001',  # 平安银行
    start='2024-01-01',
    end='2024-01-31',
    adjust='qfq'  # 前复权
)

# 获取实时快照
snapshot = manager.get_snapshot('000001')
```

### 批量获取

```python
from finshare import get_data_manager

manager = get_data_manager()

# 批量获取多只股票（使用6位代码）
codes = ['000001', '000002', '600000']
data_dict = manager.batch_get_kline(codes, start='2024-01-01')

for code, data in data_dict.items():
    print(f"{code}: {len(data)} 条数据")
```

### 使用特定数据源

```python
from finshare import EastMoneyDataSource, TencentDataSource

# 使用东方财富
eastmoney = EastMoneyDataSource()
data = eastmoney.get_kline('000001', start='2024-01-01')

# 使用腾讯财经
tencent = TencentDataSource()
data = tencent.get_kline('000001', start='2024-01-01')
```

## 🌟 为什么选择 finshare？

finshare 是 [米波量化平台](https://meepoquant.com) 的数据层，经过生产环境验证，稳定可靠。

### 完整的量化交易解决方案

如果你需要更强大的功能，可以使用米波平台：

| 功能 | finshare | 米波平台 |
|------|-----------|----------|
| 数据获取 | ✅ 免费 | ✅ |
| 策略回测 | ❌ | ✅ |
| 实时监控 | ❌ | ✅ |
| 策略市场 | ❌ | ✅ |
| 实盘交易 | ❌ | ✅ |
| 移动端 | ❌ | ✅ |

👉 [立即体验米波平台](https://meepoquant.com/signup?from=github)

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
    💡 需要完整的量化交易平台？访问 <a href="https://meepoquant.com">米波量化</a>
  </p>
</div>
