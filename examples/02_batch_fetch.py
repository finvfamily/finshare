"""
示例 2: 批量获取数据

演示如何批量获取多只股票的数据。
"""

import finshare as fs


def main():
    """运行批量数据获取示例"""

    fs.logger.info("=" * 50)
    fs.logger.info("finshare 批量数据获取示例")
    fs.logger.info("=" * 50)

    # 1. 定义股票列表（只需6位代码）
    symbols = [
        "000001",  # 平安银行
        "000002",  # 万科A
        "600000",  # 浦发银行
        "600036",  # 招商银行
    ]

    fs.logger.info(f"\n批量获取 {len(symbols)} 只股票的数据...")

    # 2. 批量获取 K线数据
    results = {}
    for symbol in symbols:
        try:
            fs.logger.info(f"\n正在获取 {symbol}...")
            data = fs.get_historical_data(code=symbol, start="2024-01-01", end="2024-01-31")

            if data is not None and len(data) > 0:
                results[symbol] = data
                fs.logger.info(f"✓ {symbol}: {len(data)} 条数据")
            else:
                fs.logger.warning(f"✗ {symbol}: 未获取到数据")

        except Exception as e:
            fs.logger.error(f"✗ {symbol}: {e}")

    # 3. 统计结果
    fs.logger.info("\n" + "=" * 50)
    fs.logger.info(f"成功获取 {len(results)}/{len(symbols)} 只股票的数据")

    # 4. 数据分析示例
    if results:
        fs.logger.info("\n数据分析:")
        for symbol, data in results.items():
            change = (data["close_price"].iloc[-1] - data["close_price"].iloc[0]) / data["close_price"].iloc[0] * 100
            fs.logger.info(f"  {symbol}: 涨跌幅 {change:+.2f}%")

    # 5. 提示
    fs.logger.info("\n💡 提示:")
    fs.logger.info("  - 获取数据后，可以使用 pandas 进行分析")
    fs.logger.info("  - 需要策略回测？访问: https://meepoquant.com")


if __name__ == "__main__":
    main()
