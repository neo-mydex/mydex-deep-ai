"""Agent 工具绑定配置（纯收集）"""

# 按模块收集所有工具
from src.tools.perp import ALL_TOOLS as PERP_TOOLS              # 1. 永续合约工具
from src.tools.coin import ALL_TOOLS as COIN_TOOLS             # 2. 代币信息工具
from src.tools.user import ALL_TOOLS as USER_TOOLS            # 3. 用户/钱包工具
from src.tools.action import ALL_TOOLS as ACTION_TOOLS          # 4. 交易 action card 工具

AGENT_TOOLS = PERP_TOOLS + COIN_TOOLS + USER_TOOLS + ACTION_TOOLS  # 所有工具全集

# 各角色可用工具集
GUEST_AVAILABLE_TOOLS = COIN_TOOLS + USER_TOOLS         # 游客：只能查询 coin 和 user 信息
USER_AVAILABLE_TOOLS = AGENT_TOOLS                             # 用户：全量（与 AGENT_TOOLS 相同，后续可按需裁剪）
ADMIN_AVAILABLE_TOOLS = AGENT_TOOLS                            # 管理员：全量
