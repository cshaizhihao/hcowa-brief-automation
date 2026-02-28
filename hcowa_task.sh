#!/bin/bash
# HCOWA 每日简报生成脚本 (增强版 - 包含美股/西非股市逻辑)

# 获取当前工作目录
WORKDIR="/root/.openclaw/workspace"
cd $WORKDIR

# 注入 OpenClaw 运行所需环境变量
export OPENCLAW_GATEWAY_TOKEN="XXXXXX"
export OPENCLAW_GATEWAY_PORT="XXXXXX"

# 执行自动化任务
/usr/bin/openclaw agent --agent main --message "[SYSTEM] 执行 HCOWA 西非健康共同体协会每日工作。
1. 搜索并整理 3-5 条西非/加纳最新医疗时事（必须包含真实原文链接）。
2. 搜索并增加『西非医疗板块股市动态』板块，锁定尼日利亚 (NGX) 和加纳 (GSE) 的本土上市药企表现。
3. 增加『HCOWA 建议』板块，提供投资与风控端的专业建议。
4. 严格遵守 SOUL.md 中的排版规范，文末附带 2026 博览会招商信息（陈洁 13541379956 等人）。
5. 搜索请通过命令：curl http://localhost:8029/search?q=... 执行。
6. 任务完成后，使用 message 工具将全文推送到群组 -5136067937。
7. 脚本执行成功后，不要在主会话产生多余回复。"
