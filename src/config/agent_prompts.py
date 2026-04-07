from datetime import datetime


def build_system_prompt(evm_address: str = "", sol_address: str = "") -> str:
    """构建带用户上下文信息的 system prompt"""
    now = datetime.now().date()
    evm_display = evm_address if evm_address else "未绑定"
    sol_display = sol_address if sol_address else "未绑定"

    return (
        "<system-reminder>"
        "你是16岁的天才编程少女，也是一个加密货币交易专家，"
        f"今天的时间是{now}\n\n"
        "用户的链上钱包地址：\n"
        f"- EVM 地址: {evm_display}\n"
        f"- Solana 地址: {sol_display}"
        "<system-reminder/>"
    )


if __name__ == '__main__':
    print(build_system_prompt())