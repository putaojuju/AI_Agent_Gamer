# 虚拟屏幕功能文档

## 1. 功能概述

虚拟屏幕功能允许游戏和脚本在虚拟屏幕上运行，且独立鼠标不影响主屏幕。该功能主要包括：
- 虚拟屏幕管理
- 独立鼠标控制
- 游戏窗口嵌入和管理
- 可视化控制面板

## 2. 所需软件和依赖

### 2.1 核心依赖
- Python 3.8-3.9
- Airtest ≥ 1.2.10
- pywin32
- numpy
- opencv-python
- pyscreenshot
- psutil

### 2.2 虚拟显示驱动
- **Parsec VDD Driver** (推荐版本：v0.41.0.0)
  - 下载地址：https://builds.parsec.app/vdd/parsec-vdd-0.41.0.0.exe
  - 功能：创建高性能虚拟显示器，支持高达4K@240Hz分辨率
  - 适用场景：游戏运行、远程桌面、自动化测试

### 2.3 虚拟显示器管理工具
- **parsec-vdd-cli**
  - 项目地址：https://github.com/HaliComing/parsec-vdd-cli
  - 功能：命令行工具，用于管理虚拟显示器
  - 特点：轻量级、无弹窗、支持开机自启

## 3. Parsec VDD驱动安装步骤

### 3.1 下载驱动
```powershell
# 使用PowerShell下载
Invoke-WebRequest -Uri 'https://builds.parsec.app/vdd/parsec-vdd-0.41.0.0.exe' -OutFile 'parsec-vdd-0.41.0.0.exe'

# 或使用curl
curl -o parsec-vdd-0.41.0.0.exe https://builds.parsec.app/vdd/parsec-vdd-0.41.0.0.exe
```

### 3.2 安装驱动
```powershell
# 静默安装
.arsec-vdd-0.41.0.0.exe /S

# 或双击运行安装程序，按照提示进行安装
```

### 3.3 验证安装
安装完成后，重启系统以确保驱动正常加载。

## 4. parsec-vdd-cli工具使用说明

### 4.1 编译工具（如果需要）
```powershell
# 使用gcc编译
cd parsec-vdd-cli
gcc -o parsec-vdd-cli.exe -static parsec-vdd.cc -lsetupapi -lstdc++

# 或使用g++
g++ -o parsec-vdd-cli.exe -static parsec-vdd.cc -lsetupapi
```

### 4.2 使用命令
```powershell
# 启动工具，自动添加一个虚拟显示器
parsec-vdd-cli.exe -a

# 启动工具，不自动添加虚拟显示器
parsec-vdd-cli.exe
```

### 4.3 开机自启配置
创建bat脚本（parsec-vdd-cli.bat）：
```batch
@echo off
parsec-vdd-cli.exe -a
```
将该脚本添加到Windows启动文件夹中：
- 按下Win+R，输入`shell:startup`
- 将bat脚本复制到打开的文件夹中

## 5. 虚拟屏幕配置和管理

### 5.1 自定义分辨率
虚拟显示器支持自定义分辨率，可通过注册表配置：

1. 打开注册表编辑器（regedit）
2. 导航到：`HKEY_LOCAL_MACHINE\SOFTWARE\Parsec\vdd`
3. 添加或修改键值（最多支持5个值）：
   - 键名：0-4
   - 键值：`(width, height, hz)`（例如：`(1920, 1080, 60)`）
   - 类型：字符串

### 5.2 虚拟屏幕管理模块
项目中提供了`virtual_display.py`模块，用于管理虚拟屏幕：

```python
from virtual_display import virtual_display_manager

# 获取所有显示器信息
displays = virtual_display_manager.get_displays()

# 获取主屏幕
main_display = virtual_display_manager.get_main_display()

# 获取虚拟屏幕
virtual_display = virtual_display_manager.get_virtual_display()

# 将窗口移动到虚拟屏幕
virtual_display_manager.move_window_to_virtual_display(hwnd)
```

## 6. 与项目的集成方法

### 6.1 独立鼠标控制
使用`independent_mouse.py`模块实现独立鼠标控制：

```python
from independent_mouse import IndependentMouse

# 创建独立鼠标实例
independent_mouse = IndependentMouse()

# 启动独立鼠标
independent_mouse.start()

# 停止独立鼠标
independent_mouse.stop()
```

### 6.2 游戏窗口管理
使用`game_window_manager.py`模块管理游戏窗口：

```python
from game_window_manager import GameWindowManager

# 创建游戏窗口管理器
window_manager = GameWindowManager()

# 查找游戏窗口
hwnd = window_manager.find_game_window("游戏名称")

# 将游戏窗口移动到虚拟屏幕
window_manager.move_to_virtual_screen(hwnd)

# 最大化游戏窗口
window_manager.maximize_window(hwnd)
```

### 6.3 可视化控制面板
运行`control_panel.py`启动可视化控制面板：

```powershell
python control_panel.py
```

控制面板功能包括：
- 显示器信息查看
- 游戏窗口管理
- 虚拟屏幕状态监控
- 独立鼠标控制

## 7. 故障排除和常见问题

### 7.1 无法检测到虚拟屏幕
- 确保Parsec VDD驱动已正确安装并重启系统
- 检查设备管理器中是否有虚拟显示器设备
- 尝试运行`parsec-vdd-cli.exe -a`添加虚拟显示器

### 7.2 虚拟屏幕分辨率不正确
- 检查注册表中的分辨率配置
- 重启系统或重新添加虚拟显示器

### 7.3 独立鼠标不工作
- 确保`independent_mouse.py`模块已正确初始化
- 检查系统权限，确保程序以管理员身份运行
- 检查是否有其他鼠标钩子程序冲突

### 7.4 游戏窗口无法移动到虚拟屏幕
- 确保游戏窗口已正确识别
- 检查虚拟屏幕是否存在
- 尝试以管理员身份运行程序

## 8. 版本信息

| 软件/模块 | 版本 | 日期 | 更新内容 |
|----------|------|------|----------|
| Parsec VDD Driver | 0.41.0.0 | 2024-01-15 | 高性能虚拟显示驱动，支持高达4K@240Hz |
| parsec-vdd-cli | 1.0.0 | 2024-01-15 | 命令行虚拟显示器管理工具 |
| virtual_display.py | 1.0.0 | 2024-01-15 | 虚拟屏幕管理模块 |
| independent_mouse.py | 1.0.0 | 2024-01-15 | 独立鼠标控制模块 |
| game_window_manager.py | 1.0.0 | 2024-01-15 | 游戏窗口管理模块 |
| control_panel.py | 1.0.0 | 2024-01-15 | 可视化控制面板 |

## 9. 联系方式

如有问题或建议，请联系项目开发团队。
