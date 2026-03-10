"""
示例 5: 特色数据获取

演示如何获取特色数据：资金流向、龙虎榜、融资融券。
"""

import finshare as fs


def main():
    """运行特色数据获取示例"""

    fs.logger.info("=" * 60)
    fs.logger.info("finshare 特色数据获取示例")
    fs.logger.info("=" * 60)

    code = "000001.SZ"  # 平安银行

    # 1. 获取资金流向
    fs.logger.info(f"\n获取 {code} 资金流向...")
    try:
        df = fs.get_money_flow(code)
        if not df.empty:
            fs.logger.info(f"✓ 成功获取资金流向数据")
            latest = df.iloc[0]
            fs.logger.info(f"  主力净流入: {latest['net_inflow_main']:,.0f} 元")
            fs.logger.info(f"  超大单净流入: {latest['net_inflow_super']:,.0f} 元")
            fs.logger.info(f"  大单净流入: {latest['net_inflow_large']:,.0f} 元")
            fs.logger.info(f"  主力净流入占比: {latest['net_inflow_main_ratio']:.2f}%")
        else:
            fs.logger.warning("未获取到资金流向数据")
    except Exception as e:
        fs.logger.error(f"获取资金流向失败: {e}")

    # 2. 获取行业资金流向
    fs.logger.info(f"\n获取行业资金流向...")
    try:
        df = fs.get_money_flow_industry()
        if not df.empty:
            fs.logger.info(f"✓ 成功获取 {len(df)} 个行业的资金流向")
            fs.logger.info(f"  行业资金流向前5:")
            for i, row in df.head(5).iterrows():
                fs.logger.info(f"    {row['industry']}: {row['change_rate']:+.2f}%")
        else:
            fs.logger.warning("未获取到行业资金流向数据")
    except Exception as e:
        fs.logger.error(f"获取行业资金流向失败: {e}")

    # 3. 获取龙虎榜
    fs.logger.info(f"\n获取龙虎榜数据...")
    try:
        df = fs.get_lhb()
        if not df.empty:
            fs.logger.info(f"✓ 成功获取 {len(df)} 条龙虎榜数据")
            fs.logger.info(f"  龙虎榜前5:")
            for i, row in df.head(5).iterrows():
                fs.logger.info(f"    {row['fs_code']}: 净买额 {row['net_buy_amount']:,.0f} 元, 原因: {row['reason'][:20]}...")
        else:
            fs.logger.warning("未获取到龙虎榜数据")
    except Exception as e:
        fs.logger.error(f"获取龙虎榜失败: {e}")

    # 4. 获取融资融券
    fs.logger.info(f"\n获取融资融券数据...")
    try:
        df = fs.get_margin()
        if not df.empty:
            fs.logger.info(f"✓ 成功获取 {len(df)} 条融资融券数据")
            latest = df.iloc[0]
            fs.logger.info(f"  日期: {latest['trade_date']}")
            fs.logger.info(f"  融资余额: {latest['rzye']:,.2f} 亿元")
            fs.logger.info(f"  融券余额: {latest['rqyl']:,.2f} 亿元")
            fs.logger.info(f"  融资买入额: {latest['rzje']:,.2f} 亿元")
        else:
            fs.logger.warning("未获取到融资融券数据")
    except Exception as e:
        fs.logger.error(f"获取融资融券失败: {e}")

    # 5. 提示
    fs.logger.info("\n" + "=" * 60)
    fs.logger.info("💡 提示:")
    fs.logger.info("  - 资金流向反映主力资金操作方向")
    fs.logger.info("  - 龙虎榜揭示机构/游资动向")
    fs.logger.info("  - 融资融券反映市场杠杆情绪")


if __name__ == "__main__":
    main()
