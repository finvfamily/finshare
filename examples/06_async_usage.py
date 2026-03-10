"""
示例 6: 异步数据获取

演示如何使用异步接口高效获取数据。
"""

import asyncio
import finshare as fs


async def main():
    """运行异步数据获取示例"""

    fs.logger.info("=" * 60)
    fs.logger.info("finshare 异步数据获取示例")
    fs.logger.info("=" * 60)

    # 1. 获取异步管理器
    async_mgr = fs.get_async_manager(max_workers=10)

    # 2. 单个异步请求
    fs.logger.info("\n异步获取单个股票快照...")
    try:
        df = await async_mgr.get_snapshot("000001.SZ")
        if not df.empty:
            fs.logger.info(f"✓ 成功获取快照")
            fs.logger.info(f"  代码: {df['fs_code'].iloc[0]}")
            fs.logger.info(f"  价格: {df['last_price'].iloc[0]}")
        else:
            fs.logger.warning("未获取到快照数据")
    except Exception as e:
        fs.logger.error(f"获取快照失败: {e}")

    # 3. 批量异步请求
    fs.logger.info("\n批量异步获取多只股票快照...")
    codes = [
        "000001.SZ",  # 平安银行
        "600519.SH",  # 贵州茅台
        "000002.SZ",  # 万科A
        "600036.SH",  # 招商银行
        "601318.SH",  # 中国平安
    ]

    try:
        df = await async_mgr.get_batch_snapshot(codes)
        if not df.empty:
            fs.logger.info(f"✓ 成功获取 {len(df)} 只股票的快照")
            fs.logger.info("\n批量获取结果:")
            for _, row in df.iterrows():
                fs.logger.info(f"  {row['fs_code']}: {row['last_price']}")
        else:
            fs.logger.warning("未获取到批量快照数据")
    except Exception as e:
        fs.logger.error(f"批量获取快照失败: {e}")

    # 4. 异步获取分钟线
    fs.logger.info("\n异步获取分钟线数据...")
    try:
        df = await async_mgr.get_minutely_data(
            "000001.SZ",
            frequency=5
        )
        if not df.empty:
            fs.logger.info(f"✓ 成功获取 {len(df)} 条分钟线数据")
            fs.logger.info(f"  时间范围: {df['trade_time'].iloc[0]} 至 {df['trade_time'].iloc[-1]}")
        else:
            fs.logger.warning("未获取到分钟线数据")
    except Exception as e:
        fs.logger.error(f"获取分钟线失败: {e}")

    # 5. 清理资源
    async_mgr.close()

    # 6. 提示
    fs.logger.info("\n" + "=" * 60)
    fs.logger.info("💡 提示:")
    fs.logger.info("  - 异步接口适合批量获取数据")
    fs.logger.info("  - 使用 ThreadPoolExecutor 实现并发")
    fs.logger.info("  - max_workers 控制并发数")


if __name__ == "__main__":
    asyncio.run(main())
