"""
示例 1: 基础数据获取

演示如何使用 finshare 获取金融数据。
"""

import finshare as fs


def main():
    """运行基础数据获取示例"""

    fs.logger.info("=" * 50)
    fs.logger.info("finshare 基础数据获取示例")
    fs.logger.info("=" * 50)

    # 1. 获取 K线数据（直接使用 fs.get_historical_data）
    symbol = "000001"  # 平安银行（只需6位代码）
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    fs.logger.info(f"\n获取 {symbol} 的 K线数据...")
    fs.logger.info(f"时间范围: {start_date} 至 {end_date}")
    try:
        data = fs.get_historical_data(
            code=symbol, start=start_date, end=end_date, adjust="qfq"  # 前复权
        )

        if data is not None and len(data) > 0:
            fs.logger.info(f"✓ 成功获取 {len(data)} 条数据")
            fs.logger.info(f"\n数据预览:")
            fs.logger.info(data.head())
            fs.logger.info(f"\n数据统计:")
            fs.logger.info(f"  开盘价: {data['open_price'].iloc[0]:.2f}")
            fs.logger.info(f"  收盘价: {data['close_price'].iloc[-1]:.2f}")
            fs.logger.info(f"  最高价: {data['high_price'].max():.2f}")
            fs.logger.info(f"  最低价: {data['low_price'].min():.2f}")
        else:
            fs.logger.warning("未获取到数据")

    except Exception as e:
        fs.logger.error(f"获取数据失败: {e}")

    # 2. 获取实时快照（直接使用 fs.get_snapshot_data）
    fs.logger.info(f"\n获取 {symbol} 的实时快照...")

    try:
        snapshot = fs.get_snapshot_data(symbol)

        if snapshot:
            fs.logger.info(f"✓ 成功获取快照数据")
            fs.logger.info(f"  股票代码: {snapshot.code}")
            fs.logger.info(f"  最新价格: {snapshot.last_price}")
            fs.logger.info(f"  成交量: {snapshot.volume}")
            fs.logger.info(f"  成交额: {snapshot.amount}")
            if snapshot.prev_close:
                change_percent = (snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100
                fs.logger.info(f"  涨跌幅: {change_percent:.2f}%")
        else:
            fs.logger.warning("未获取到快照数据")

    except Exception as e:
        fs.logger.error(f"获取快照失败: {e}")

    # 3. 提示
    fs.logger.info("\n" + "=" * 50)
    fs.logger.info("💡 下一步:")
    fs.logger.info("  - 查看更多示例: examples/")
    fs.logger.info("  - 阅读文档: https://finshare.readthedocs.io")
    fs.logger.info("  - 需要策略回测？访问: https://meepoquant.com")


if __name__ == "__main__":
    main()
