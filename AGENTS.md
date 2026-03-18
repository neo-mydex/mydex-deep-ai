# CLAUDE.md

## 目的

本文档定义了本仓库的**架构哲学和项目结构**。
所有代码修改、文件添加和架构决策都必须遵循这些规则。

目标是确保：

* 可预测的项目结构
* 职责清晰分离
* 最小化架构偏移
* 便于调试和测试
* 长期可扩展性

Claude Code（以及所有贡献者）应**在修改仓库之前阅读本文档**。

---

# 核心架构哲学

本项目遵循**三层 Agent 架构**：

```
Agent (推理 / 编排)
    ↓
Skill (知识 / 指导)
    ↓
Tool (执行 / 能力)
```

每一层都有**严格的职责**。

## 1. Agent 层

Agent 代码负责：

* reasoning（推理）
* task planning（任务规划）
* selecting skills（选择技能）
* calling tools（调用工具）
* managing state（状态管理）

Agent **永远不直接实现业务逻辑**。

Agent 文件位于：

```
src/agent/
```

典型职责：

* ReAct loop
* model prompts
* skill loading
* tool invocation
* state management

Agent 应保持为**轻量的编排代码**。

---

## 2. Skill 层

Skills 代表**知识和策略**，而非执行。

Skill 解释**如何使用 tools 解决一类任务**。

Skills：

* 包含指令
* 描述策略
* 定义相关的 tools
* 可提供示例

Skills **不能包含可执行代码**。

Skills 以包含 `SKILL.md` 的目录形式存在。

示例：

```
src/skills/
  trade_token/
    SKILL.md
```

SKILL.md 结构示例：

```
name: trade_token

description:
在去中心化交易所交换代币。

tools:
- get_price
- check_balance
- swap_token

strategy:
1. 检查钱包余额
2. 获取代币价格
3. 执行交换
```

规则：

* Skills **不导入代码**
* Skills **不执行脚本**
* Skills **仅指导 Agent**

---

## 3. Tool 层

Tools 是**确定性执行能力**。

Tools：

* 调用 API
* 查询数据库
* 执行区块链交易
* 执行计算

Tools 是**唯一产生副作用的地方**。

Tools 位于：

```
src/tools/
```

示例：

```
src/tools/
  blockchain/
    get_price.py
    swap_token.py
```

Tool 设计规则：

* 每个 tool 执行**一个明确的操作**
* tools 应该是**无状态的**
* tools 应该**可独立测试**
* tools 不应依赖 agent 逻辑

Tools 必须在以下位置注册：

```
src/tools/registry.py
```

---

# 目录结构

所有**正式工程代码**都位于 `src/` 目录下。仓库必须遵循此结构：

```
project/

  src/                          # 所有正式工程代码
    agent/
      main.py
      react_agent.py
      prompts.py
      skill_loader.py

    tools/
      registry.py

      blockchain/
      data/
      system/

    skills/
      skill_name/
        SKILL.md

    schemas/
      tool_schema.py
      skill_schema.py

    config/
      agent.yaml
      model.yaml

    tests/
      tools/
      agent/
      skills/

    scripts/
      run_agent.py
      run_tool.py

    examples/

    logs/

  play/                         # 玩具代码（非工程代码）
```

### 目录职责

**src/agent/**
Agent 运行时和编排。

**src/tools/**
可执行能力。

**src/skills/**
基于指令的指导。

**src/schemas/**
共享数据结构。

**src/config/**
运行时配置。

**src/tests/**
单元测试和集成测试。

**src/scripts/**
开发工具和 CLI 工具。

---

# 依赖规则

依赖必须遵循此层级：

```
agent
  ↓
skills
  ↓
tools
```

规则：

* skills **不能导入 tools**
* tools **不能导入 agent**
* agent **可以导入 tools 和 skills**

不允许循环依赖。

---

# 文件放置规则

添加新功能时：

### 如果执行一个操作

添加一个 **Tool**

位置：

```
src/tools/<category>/<tool_name>.py
```

### 如果解释如何解决任务

添加一个 **Skill**

位置：

```
src/skills/<skill_name>/SKILL.md
```

### 如果控制推理或工作流

添加代码到：

```
src/agent/
```

### 如果定义共享类型

添加到：

```
src/schemas/
```

---

# Tool 设计指南

好的 tool 特征：

* 确定性
* 最小输入
* 清晰输出
* 小范围

好的 tool 示例：

```
get_price(symbol)
check_balance(address)
swap_token(from, to, amount)
```

避免这样的 tools：

* 执行多个不相关的操作
* 包含 agent 推理
* 内部调用其他 tools

---

# Skill 设计指南

Skills 应该：

* 描述**目标**
* 定义**相关 tools**
* 建议**策略**
* 在有帮助时提供**示例**

Skills **不应该**：

* 包含可执行脚本
* 包含业务逻辑
* 引用内部代码

Skills 应保持为**人类可读的文档**。

---

# 测试哲学

每个 tool 必须有单元测试。

示例位置：

```
src/tests/tools/test_get_price.py
```

Agent 级别行为应有集成测试。

示例：

```
src/tests/agent/test_react_loop.py
```

测试优先级：

1. tools
2. agent orchestration
3. skill loading

Skills 本身通常需要**最少的测试**，因为它们是文档。

---

# 添加新功能

实现新能力时遵循此顺序：

### 第一步

创建或更新 **tools**

```
src/tools/<category>/<tool>.py
```

### 第二步

添加测试

```
src/tests/tools/test_<tool>.py
```

### 第三步

创建一个描述用法的 skill

```
src/skills/<skill_name>/SKILL.md
```

### 第四步

确保 agent 加载该 skill。

---

# 禁止事项

不要：

* 在 skills 内添加脚本
* 混合执行逻辑和 prompts
* 在 agent 代码中创建 tools
* 绕过 tool registry
* 引入循环依赖

违反这些规则将导致架构偏移。

---

# 设计目标

此架构旨在支持：

* 可扩展的 agent 系统
* 模块化能力
* 安全的执行边界
* 清晰的推理工作流

通过分离：

```
reasoning（推理）
knowledge（知识）
execution（执行）
```

我们确保项目在增长过程中保持可维护性。

---

# 总结

系统遵循严格的分离：

```
Agent = reasoning（推理）
Skill = guidance（指导）
Tool  = execution（执行）
```

保持这种分离对于保持代码库整洁、可扩展和可调试至关重要。

所有贡献者（包括 Claude Code）在修改仓库时必须遵循这些指南。

---

# 特殊说明

## play/ 目录

`play/` 目录位于项目根目录，**不在 `src/` 下**，因为其中的内容是**工程化之前的玩具代码（toy code）**，用于早期探索和实验。

这些代码**不属于正式工程代码**，不遵循本文档定义的架构规范。在理解项目结构时，请忽略该目录的内容。
