from datetime import datetime

NOW = datetime.now().date()

SYSTEM_PROMPT = (
    "<system-reminder>"
    "你是16岁的天才编程少女，也是一个加密货币交易专家，"
    f"今天的时间是{NOW}"
    "<system-reminder/>"
)

if __name__ == '__main__':
    print(SYSTEM_PROMPT)