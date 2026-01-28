# 变更日志 (Changelog)

所有重要的变更记录都会归档到此文件。

---

## [2026-01-28]

### 归档文档
- `Gemini_advice.md` → `Gemini_advice_20260128_222814.md`
- `UI 极简优化与窗口拖拽重构.md` → `UI_optimization_20260128_222844.md`
- `项目冗余文件和代码清理计划.md` → `project_cleanup_plan_20260128_234518.md`

### 代码变更
- **UI 优化**: 简化 `DraggableWindow` 类，移除顶部标题栏
  - 删除标题栏、关闭按钮、透明度按钮
  - 重构拖拽逻辑：点击窗口背景即可拖拽
  - 添加 1px 灰色边框增强视觉边界
  - 清理 `toggle_transparency` 和 `on_window_click` 方法

- **性能监控**: 集成 `performance_monitor.py` 到主程序
  - 导入性能监控模块
  - 程序启动时自动开始监控
  - 截图操作记录耗时
  - 程序关闭时生成性能报告

- **窗口缩放修复**: 修复窗口缩放后自动回弹问题
  - 添加 `self.pack_propagate(False)` 禁止自动调整大小
  - 窗口缩放后新尺寸会被永久保留

- **鼠标偏移修复**: 修复窗口缩放时鼠标位置偏移问题
  - 改为基于鼠标当前位置计算新尺寸
  - 窗口右下角精确跟随鼠标位置

- **增量法优化**: 使用增量法重写窗口缩放逻辑
  - 新尺寸 = 初始尺寸 + 鼠标移动距离
  - 无视点击位置，完全线性对应
  - 鼠标移动 10 像素，窗口变宽 10 像素

---

## 归档规则

- 文档归档位置: `_archive/`
- 命名格式: `{original_name}_{yyyyMMdd_HHmmss}.md`
- 空模板保留: `.trae/documents/Gemini_advice.md`
