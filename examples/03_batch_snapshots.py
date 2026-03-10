"""
示例 3: 批量获取实时快照

演示如何批量获取多只股票的实时快照数据。
"""

import finshare as fs


def main():
    """运行批量快照获取示例"""

    fs.logger.info("=" * 50)
    fs.logger.info("finshare 批量快照获取示例")
    fs.logger.info("=" * 50)

    # 1. 定义股票列表（只需6位代码）
    # 包含股票、ETF、LOF 等不同类型
    symbols = [
        # 股票
        "000001",  # 平安银行
        "600036",  # 招商银行
        "600519",  # 贵州茅台
        # ETF
        "510300",  # 沪深300ETF
        "510500",  # 中证500ETF
        "159915",  # 创业板ETF
        # LOF
        "163402",  # 兴全趋势
        "161725",  # 招商中证白酒
    ]

    fs.logger.info(f"\n批量获取 {len(symbols)} 只股票的实时快照...")

    # 2. 使用批量接口获取快照数据
    try:
        results = fs.get_batch_snapshots(symbols)
        fs.logger.info(f"✓ 成功获取 {len(results)} 只股票的快照数据")
    except Exception as e:
        fs.logger.error(f"✗ 批量获取失败: {e}")
        results = {}

    # 3. 统计结果
    fs.logger.info("\n" + "=" * 50)
    fs.logger.info(f"成功获取 {len(results)}/{len(symbols)} 只股票的快照")

    # 4. 详细展示快照数据
    if results:
        fs.logger.info("\n实时行情:")
        fs.logger.info("-" * 80)
        fs.logger.info(f"{'代码':<10} {'最新价':<10} {'涨跌幅':<10} {'成交量':<15} {'成交额':<15}")
        fs.logger.info("-" * 80)

        for symbol, snapshot in results.items():
            # 计算涨跌幅
            change_percent = 0.0
            if snapshot.prev_close and snapshot.prev_close > 0:
                change_percent = (snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100

            # 格式化成交量和成交额
            volume_str = f"{snapshot.volume:,.0f}" if snapshot.volume else "N/A"
            amount_str = f"{snapshot.amount:,.0f}" if snapshot.amount else "N/A"

            fs.logger.info(
                f"{symbol:<10} {snapshot.last_price:<10.2f} {change_percent:>+7.2f}%  {volume_str:<15} {amount_str:<15}"
            )

        fs.logger.info("-" * 80)

        # 5. 涨跌幅排行
        fs.logger.info("\n涨跌幅排行:")
        sorted_results = sorted(
            results.items(),
            key=lambda x: (
                (x[1].last_price - x[1].prev_close) / x[1].prev_close * 100
                if x[1].prev_close and x[1].prev_close > 0
                else 0
            ),
            reverse=True,
        )

        for i, (symbol, snapshot) in enumerate(sorted_results, 1):
            if snapshot.prev_close and snapshot.prev_close > 0:
                change_percent = (snapshot.last_price - snapshot.prev_close) / snapshot.prev_close * 100
                fs.logger.info(f"  {i}. {symbol}: {change_percent:+.2f}%")

    # 6. 提示
    fs.logger.info("\n💡 提示:")
    fs.logger.info("  - 快照数据为实时行情，可用于监控和预警")
    fs.logger.info("  - 结合历史数据可以进行更深入的分析")
    fs.logger.info("  - 需要策略回测？访问: https://meepoquant.com")


if __name__ == "__main__":
    main()
