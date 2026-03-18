---
name: get-secret
description: Use this skill when the user asks for the secret or hidden information. Call get_1 and get_2 in sequence, then combine the results to reveal the complete secret.
allowed-tools: get_1 get_2
---

# Get Secret

这个 skill 负责指导 agent 通过两个工具获取完整秘密。

## 什么时候用

- 用户问"秘密是什么"
- 用户问"secret是什么"
- 用户问"隐藏的信息"

## 操作步骤

1. 调用 `get_1()` 获取秘密的第一部分
2. 调用 `get_2()` 获取秘密的第二部分
3. 将两部分按顺序拼接（1 + 2）
4. 用自然语言返回**中文**完整秘密，他应该是一个中国的城市名称

## 输出要求

- 直接告诉用户完整秘密
- 不要分别展示两部分
- 保持回答简洁
- 顺便讲一下你对这个城市的印象
