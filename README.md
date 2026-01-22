# Game_Script

游戏脚本自动化框架 - 基于Airtest的多游戏脚本自动化系统，集成AI视觉识别能力，支持虚拟屏幕运行和独立鼠标控制，确保脚本稳定、高效、安全运行。

## 功能特性

### 核心功能
- **AI 视觉识别**：集成豆包-1.8-Vision 模型，实现智能画面分析和决策
- **智能回退机制**：当传统模板匹配失败时，AI 自动接管处理未知状态
- **后台运行模式**：基于窗口消息（PostMessage）的真正后台操作，不影响前台
- **虚拟屏幕支持**：使用Parsec VDD Driver实现虚拟屏幕，支持多游戏同时运行
- **独立鼠标控制**：实现独立鼠标控制器，支持鼠标瞬移和后台点击
- **脚本管理器**：现代化仪表板UI界面，支持脚本管理、运行和监控
- **截图工具**：支持实时截图、历史记录管理、魔棒去背景功能
- **性能监控**：实时监控脚本运行性能，包括CPU、内存、截图耗时等
- **多游戏支持**：支持多个游戏的自动化脚本，易于扩展

### AI 功能详解
- **视觉分析**：AI 分析游戏界面，识别按钮、弹窗和复杂状态
- **智能决策**：根据界面状态自动选择最佳操作（点击/等待/停止）
- **坐标归一化**：支持不同分辨率的自动适配（0.0-1.0 相对坐标）
- **调试快照**：自动保存 AI 决策截图，包含红色标记指示点击位置
- **熔断保护**：连续多次 AI 干预无效时自动停止，防止无限循环

## 核心模块

### AI 大脑模块
- **ai_brain.py**：豆包视觉模型封装
  - OpenAI 兼容接口（火山引擎 Ark 平台）
  - Base64 图像编码和压缩
  - 归一化坐标转换
  - 自动调试快照保存
  - 连接测试功能

### 脚本管理器
- **script_manager.py**：现代化仪表板 UI
  - Sidebar + Dashboard 布局
  - 深色主题日志查看器
  - AI 配置管理（API Key、Endpoint ID）
  - 连接测试功能
  - AI 思考和操作日志标签

### 后台窗口模块
- 实现基于窗口消息的后台点击
- 支持PostMessage和SendInput两种点击方法
- 自动坐标转换和窗口检测

### 截图工具
- **screenshot_tool.py**：截图工具
  - 实时截图和历史记录
  - 魔棒去背景功能
  - 灰度和二值化预览
  - 自动生成 Airtest 代码

### 独立鼠标控制
- 独立鼠标控制器
- 支持鼠标瞬移和后台点击
- 不影响前台鼠标操作

### 虚拟屏幕管理
- 虚拟屏幕检测和管理
- 支持多显示器环境
- 窗口位置自动调整

### 性能监控
- 实时性能监控
- 截图和点击耗时统计
- 资源使用情况记录

## 安装

### 环境要求
- Python 3.8-3.9
- Windows 10/11
- Airtest ≥1.2.10
- 火山引擎 API Key（用于 AI 功能）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 虚拟屏幕驱动
1. 下载Parsec VDD Driver: https://builds.parsec.app/vdd/parsec-vdd-0.41.0.0.exe
2. 安装驱动并重启电脑
3. 使用parsec-vdd-cli管理虚拟屏幕

## 使用方法

### 脚本管理器
```bash
python script_manager.py
```

### 配置 AI 功能
1. 启动脚本管理器
2. 点击"⚙️ 设置"按钮
3. 在"AI 配置"区域填写：
   - 火山引擎 API Key
   - 模型端点 ID (Endpoint ID)
   - 模型名称（默认：Doubao-1.8-Pro）
4. 点击"🔗 测试 AI 连接"验证配置

### 运行游戏脚本
```bash
python games/Girls_Creation_script/dungeon/dungeon.py --window-title="游戏窗口标题" --window-hwnd=窗口句柄
```

### 测试脚本
```bash
python test_files/test_game_click_strict.py
```

## 项目结构

```
Game_Script/
├─ ai_brain.py               # AI 视觉识别核心模块
├─ background_windows.py       # 后台窗口模块
├─ independent_mouse.py        # 独立鼠标控制
├─ virtual_display.py          # 虚拟屏幕管理
├─ performance_monitor.py      # 性能监控
├─ script_manager.py           # 脚本管理器（现代化 UI）
├─ screenshot_tool.py         # 截图工具（含魔棒去背景）
├─ log_formatter.py          # 日志格式化器
├─ requirements.txt           # 依赖列表
├─ screenshot_config.json    # 配置文件（含 AI 配置）
└─ games/                   # 游戏脚本目录
   ├─ Girls_Creation_script/
   │  ├─ daily/             # 日常任务脚本
   │  └─ dungeon/           # 地牢脚本（含 AI 智能回退）
   └─ twinkle_starknightsX_script/
      └─ daily/              # 日常任务脚本
```

## 技术特点

### AI 视觉识别
- 豆包-1.8-Vision 模型（通过火山引擎 Ark 平台）
- OpenAI 兼容接口
- Base64 图像编码和压缩（最大 1280px）
- 归一化坐标系统（0.0-1.0 → 像素坐标）
- 自动调试快照（带红色标记）
- 熔断保护机制（连续 3 次无效后停止）

### PostMessage点击
- 基于Windows消息队列
- 不影响前台操作
- 适合后台自动化

### SendInput点击
- 模拟真实鼠标硬件事件
- 触发完整的点击特效
- 适合需要真实交互的场景

### 坐标转换
- 精确的屏幕坐标到窗口客户区坐标转换
- 支持最大化和非最大化窗口
- 自动窗口检测和位置调整

## AI 集成示例

### 在脚本中使用 AI 智能回退

```python
from ai_brain import DoubaoBrain

# 加载 AI 配置并初始化大脑
brain = DoubaoBrain(api_key="your_api_key", endpoint_id="ep-xxxxx")

# 当传统识别失败时，调用 AI 求解
result = brain.analyze(screenshot, "请分析当前界面并点击继续按钮")

if result['action'] == 'click':
    # 转换归一化坐标为像素坐标
    pixel_x, pixel_y = brain.normalize_to_pixel(
        result['target'][0], result['target'][1],
        window_width, window_height
    )
    api.touch((pixel_x, pixel_y))
```

### 调试快照

AI 决策会自动保存到 `logs/ai_snapshots/` 目录：
- 文件名格式：`YYYYMMDD_HHMMSS_action_x_y.jpg`
- 包含红色标记指示 AI 决策的点击位置
- 自动清理（超过 100 张时删除最旧的）

## 测试结果

经过测试验证，PostMessage方法虽然不会触发鼠标点击特效，但确实能作用在游戏按钮上，说明游戏引擎虽然绕过了Windows消息队列的视觉反馈，但仍能响应窗口消息中的点击事件。

AI 视觉识别在处理未知状态和复杂界面时表现出色，能够准确识别按钮位置并做出合理决策。

## 许可证

MIT License

## 作者

putaojuju

## 相关链接

- [My_Script](https://github.com/putaojuju/My_Script) - 具体游戏脚本
- [Airtest](https://airtest.net/) - 自动化测试框架
- [Parsec VDD](https://github.com/HaliComing/parsec-vdd-cli) - 虚拟屏幕驱动
- [火山引擎 Ark](https://www.volcengine.com/docs/product/ark) - 豆包模型 API 平台