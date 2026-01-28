## 执行计划：修复窗口缩放回弹问题

### 问题
使用鼠标左键调整窗口大小时，窗口会在松开鼠标后自动回弹到原始大小。

### 原因
`tkinter/customtkinter` 的 Frame 默认启用了几何传播 (Geometry Propagation)，容器会自动收缩/扩张以包裹内部子控件，忽略手动设置的 width 和 height。

### 解决方案
在 `DraggableWindow.__init__` 中添加 `self.pack_propagate(False)`，禁止 Pack 布局管理器自动调整窗口大小。

### 修改步骤

#### 步骤 1: 修改 `DraggableWindow.__init__`
在 `main.py` 的 `DraggableWindow` 类的 `__init__` 方法中，在 `super().__init__()` 之后添加：
```python
# 禁止 Pack 布局管理器自动调整窗口大小
self.pack_propagate(False)
```

### 涉及文件
- `main.py`

### 预期效果
- 窗口缩放后，新尺寸会被永久保留
- 不再随内容自动收缩/扩张

### 归档
- 扫描 `.trae/documents/` 目录
- 调用 AutoArchive Skill 归档文档
- 更新 Changelog