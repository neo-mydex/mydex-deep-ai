"""
测试 src/config/tools.py 的 Agent 工具绑定配置
"""

from src.config.tools import AGENT_TOOLS


def test_agent_tools_not_empty():
    """Agent 工具列表不能为空"""
    assert len(AGENT_TOOLS) > 0


def test_agent_tools_are_callable():
    """Agent 工具列表中的项都应该可调用"""
    for tool in AGENT_TOOLS:
        assert callable(tool)


def test_agent_tools_no_duplicate_names():
    """避免重复注册同名工具，减少模型选择歧义"""
    names = [getattr(tool, "name", None) for tool in AGENT_TOOLS]
    assert all(isinstance(name, str) and len(name) > 0 for name in names)
    assert len(names) == len(set(names))
