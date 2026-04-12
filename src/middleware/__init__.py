"""
Agent 中间件配置

模仿 agent_tools.py 模式，统一收集中间件。
"""

from src.config.agent_tools import AGENT_TOOLS
from .dynamic_tools import DynamicToolsMiddleware

AGENT_MIDDLEWARES = [
    DynamicToolsMiddleware(),
]
