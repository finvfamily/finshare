# finshare Examples

本目录包含 finshare 的使用示例。

## 示例列表

### 01_basic_usage.py
基础数据获取示例，演示如何：
- 获取数据管理器
- 获取 K线数据
- 获取实时快照
- 查看数据统计

```bash
python examples/01_basic_usage.py
```

### 02_batch_fetch.py
批量数据获取示例，演示如何：
- 批量获取多只股票数据
- 处理获取失败的情况
- 进行简单的数据分析

```bash
python examples/02_batch_fetch.py
```

### 03_batch_snapshots.py
批量快照示例，演示如何：
- 批量获取多只股票实时快照
- 并发获取优化

```bash
python examples/03_batch_snapshots.py
```

### 04_financial_data.py
财务数据示例，演示如何：
- 获取利润表数据
- 获取资产负债表数据
- 获取现金流量表数据
- 获取财务指标

```bash
python examples/04_financial_data.py
```

### 05_feature_data.py
特色数据示例，演示如何：
- 获取资金流向数据
- 获取行业资金流向
- 获取龙虎榜数据
- 获取融资融券数据

```bash
python examples/05_feature_data.py
```

### 06_async_usage.py
异步数据获取示例，演示如何：
- 使用异步接口获取数据
- 批量并发获取
- 高效处理大量股票

```bash
python examples/06_async_usage.py
```

### 07_cache_usage.py
缓存与稳定性示例，演示如何：
- 使用缓存装饰器减少API调用
- 使用熔断器防止故障传播
- 使用智能路由选择最佳数据源
- 使用监控系统掌握数据源状态

```bash
python examples/07_cache_usage.py
```

## 运行示例

### 前提条件

确保已安装 finshare：

```bash
pip install finshare
```

或从源码安装：

```bash
cd /path/to/finshare
pip install -e .
```

### 运行单个示例

```bash
python examples/01_basic_usage.py
```

### 运行所有示例

```bash
for file in examples/*.py; do
    echo "Running $file..."
    python "$file"
    echo ""
done
```

## 注意事项

1. **数据获取**
   - 使用公开数据源，可能有访问频率限制
   - 建议在非交易时间运行示例
   - 部分数据源可能需要网络连接

2. **数据使用**
   - 获取的数据仅供学习和研究使用
   - 实盘交易请使用专业平台
   - 历史数据不代表未来表现

3. **完整功能**
   - finshare 只提供数据获取功能
   - 需要策略回测？访问 [米波平台](https://meepoquant.com)
   - 需要实盘交易？访问 [米波平台](https://meepoquant.com)

## 更多资源

- **GitHub**: https://github.com/finvfamily/finshare
- **官网**: https://meepoquant.com
- **完整平台**: https://meepoquant.com

## 贡献示例

欢迎贡献新的示例！请参考 [贡献指南](../CONTRIBUTING.md)。

示例要求：
- 清晰的注释和文档
- 完整的错误处理
- 实用的使用场景
- 符合代码规范
