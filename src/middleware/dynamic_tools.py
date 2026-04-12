"""
Agent 中间件：动态工具过滤

根据 context.role 判断用户角色，返回对应的工具列表。
"""

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from typing import Any, Callable

from src.config.agent_context import ChatContext, UserRole, InteractMode
from src.config.agent_tools import (
    GUEST_AVAILABLE_TOOLS,
    USER_AVAILABLE_TOOLS,
    ADMIN_AVAILABLE_TOOLS,
    ACTION_TOOLS,
)


class DynamicToolsMiddleware(AgentMiddleware):
    """根据 context.role 返回对应角色的工具集。

    - action 工具（src/tools/action）仅在 InteractMode.FRONTEND 模式下可用
    """

    # 角色 → 工具集 映射
    _TOOLS_BY_ROLE = {
        UserRole.GUEST: GUEST_AVAILABLE_TOOLS,
        UserRole.USER: USER_AVAILABLE_TOOLS,
        UserRole.ADMIN: ADMIN_AVAILABLE_TOOLS,
    }

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        role = self._resolve_role(request)
        mode = self._resolve_interact_mode(request)
        request = self._filter_tools(request, role, mode)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Any],
    ) -> Any:
        role = self._resolve_role(request)
        mode = self._resolve_interact_mode(request)
        request = self._filter_tools(request, role, mode)
        return await handler(request)

    def _resolve_role(self, request: ModelRequest) -> UserRole:
        ctx = getattr(request.runtime, "context", None) if request.runtime else None
        if ctx is None:
            return UserRole.GUEST
        return ctx.role

    def _resolve_interact_mode(self, request: ModelRequest) -> InteractMode:
        ctx = getattr(request.runtime, "context", None) if request.runtime else None
        if ctx is None:
            return InteractMode.FRONTEND
        return ctx.interact_mode

    def _filter_tools(
        self,
        request: ModelRequest,
        role: UserRole,
        mode: InteractMode,
    ) -> ModelRequest:
        if request.tools is None:
            return request

        # 第一步、角色决定范围
        allowed = list(self._TOOLS_BY_ROLE.get(role, GUEST_AVAILABLE_TOOLS))

        # 第二步、仅 FRONTEND 模式放行 action 工具
        if mode != InteractMode.FRONTEND:
            allowed = [t for t in allowed if t not in ACTION_TOOLS]

        allowed_names = {t.name for t in allowed}
        filtered = [t for t in request.tools if getattr(t, "name", None) in allowed_names]
        return request.override(tools=filtered)


if __name__ == "__main__":
    """打印不同 context 下的可用工具"""

    # uv run python -m src.middleware.dynamic_tools

    from src.config.agent_tools import AGENT_TOOLS

    mw = DynamicToolsMiddleware()

    roles = [UserRole.GUEST, UserRole.USER, UserRole.ADMIN]
    modes = [InteractMode.FRONTEND, InteractMode.WEBAPI, InteractMode.CLI]

    class FakeRequest:
        def __init__(self, tools):
            self.tools = tools

        def override(self, tools):
            return FakeRequest(tools=tools)

    for role in roles:
        for mode in modes:
            req = FakeRequest(list(AGENT_TOOLS))
            # 直接调用 _filter_tools，绕过 override 链路
            result = mw._filter_tools(req, role, mode)
            names = sorted(getattr(t, "name", None) for t in result.tools)
            print(f"[role={role.value}, mode={mode.value}] ({len(names)} tools)")
            for n in names:
                print(f"  - {n}")
            print()
