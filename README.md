# 🤖 AI Agent Gamer

基于 ReAct 架构的游戏自动化 AI Agent，支持多游戏知识库和智能决策。

## ✨ 核心特性

- **ReAct 架构**：思考-行动-观察循环，实现智能决策
- **多游戏支持**：通过知识库系统支持不同游戏
- **OCR 文字定位**：优先使用文字锚点，提高点击精度
- **SoM 网格标注**：4x4 网格辅助 AI 坐标估算
- **LangChain 集成**：使用 LangChain 的 Tool 系统封装操作
- **视觉反馈验证**：严禁硬等待，必须使用视觉反馈

## 🛠 技术栈

- **Python**: 3.11
- **环境管理**: Conda
- **AI 模型**: 豆包 Pro (Doubao-1.8-Pro)
- **OCR 引擎**: RapidOCR
- **Agent 框架**: LangChain
- **API**: 火山引擎 Ark

## 📁 项目结构

```
Root/
├─ knowledge/          # 游戏知识库 (JSON)
├─ vision_core.py      # 视觉核心 (RapidOCR + SoM)
├─ knowledge_manager.py # 知识库管理
├─ skills_registry.py  # 技能注册表 (LangChain Tools)
├─ agent_core.py      # Agent 核心 (ReAct 架构)
└─ script_manager.py  # AI Agent 控制台
```

## 🚀 快速开始

### 环境准备

```bash
# 激活 Conda 环境
conda activate ai_agent_311

# 安装依赖
pip install -r requirements.txt
```

### 运行控制台

```bash
python script_manager.py
```

### 添加游戏知识库

在 `knowledge/` 目录下创建 JSON 文件：

```json
{
  "按钮名称": "操作说明",
  "资源名称": "获取方式"
}
```

## 🧠 ReAct 架构设计

Agent 使用 ReAct (Reasoning + Acting) 循环：

1. **观察**：获取当前截图和知识库信息
2. **思考**：分析当前状态，决定下一步操作
3. **行动**：选择并执行工具（click_text, key_press 等）
4. **观察**：获取操作结果，验证是否成功
5. **循环**：重复上述步骤，直到完成任务

## 📝 开发规范

1. 所有新功能必须封装为 Tool 供 Agent 调用
2. 不同游戏必须在 `knowledge/` 下建立独立 JSON
3. 严禁使用 `time.sleep` 硬等待，必须使用视觉反馈验证
4. 坐标操作优先使用 OCR 文字锚点，其次使用网格坐标

## 🔧 常见问题

### Q: 如何添加新游戏支持？

A: 在 `knowledge/` 目录下创建 `游戏名.json` 文件，添加游戏相关的知识和操作说明。

### Q: OCR 识别不准确怎么办？

A: Agent 会自动降级使用网格坐标，可以在知识库中添加更准确的文字描述。

### Q: 如何调试 Agent 决策？

A: 查看 `log/agent_core.log` 文件，包含完整的思维链和操作日志。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 仓库管理

- **公开仓库**: https://github.com/putaojuju/AI_Agent_Gamer
- **私有仓库**: https://github.com/putaojuju/My_Script (游戏脚本)

---

**版本**: v2.0.0 (ReAct 架构重构)
