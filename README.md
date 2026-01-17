# Game_Script

游戏脚本自动化框架 - 基于Airtest的多游戏脚本自动化系统，支持虚拟屏幕运行和独立鼠标控制，确保脚本稳定、高效、安全运行。

## 功能特性

- 后台运行模式：基于窗口消息（PostMessage）的真正后台操作，不影响前台
- 虚拟屏幕支持：使用Parsec VDD Driver实现虚拟屏幕，支持多游戏同时运行
- 独立鼠标控制：实现独立鼠标控制器，支持鼠标瞬移和后台点击
- 脚本管理器：可视化UI界面，支持脚本管理、运行和监控
- 性能监控：实时监控脚本运行性能，包括CPU、内存、截图耗时等
- 多游戏支持：支持多个游戏的自动化脚本，易于扩展

## 核心模块

### 后台窗口模块
- 实现基于窗口消息的后台点击
- 支持PostMessage和SendInput两种点击方法
- 自动坐标转换和窗口检测

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

### 运行游戏脚本
```bash
python run_game_script.py
```

### 测试脚本
```bash
python test_files/test_game_click_strict.py
```

## 项目结构

```
Game_Script/
├─ background_windows.py         # 后台窗口模块
├─ independent_mouse.py          # 独立鼠标控制
├─ virtual_display.py            # 虚拟屏幕管理
├─ performance_monitor.py        # 性能监控
├─ script_manager.py             # 脚本管理器
├─ control_panel.py             # 控制面板
├─ game_window_manager.py        # 游戏窗口管理
├─ run_game_script.py           # 脚本运行器
├─ requirements.txt             # 依赖列表
└─ test_files/                # 测试文件目录
```

## 技术特点

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

## 测试结果

经过测试验证，PostMessage方法虽然不会触发鼠标点击特效，但确实能作用在游戏按钮上，说明游戏引擎虽然绕过了Windows消息队列的视觉反馈，但仍能响应窗口消息中的点击事件。

## 许可证

MIT License

## 作者

putaojuju

## 相关链接

- [My_Script](https://github.com/putaojuju/My_Script) - 具体游戏脚本
- [Airtest](https://airtest.net/) - 自动化测试框架
- [Parsec VDD](https://github.com/HaliComing/parsec-vdd-cli) - 虚拟屏幕驱动
