"""Agent 工具绑定配置（纯收集）"""
from src.tools.perp import ALL_TOOLS as PERP_TOOLS
from src.tools.coin import ALL_TOOLS as COIN_TOOLS
from src.tools.user import ALL_TOOLS as USER_TOOLS

AGENT_TOOLS = PERP_TOOLS + COIN_TOOLS + USER_TOOLS
