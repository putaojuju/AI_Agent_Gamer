## 执行计划：使用增量法修复窗口缩放鼠标偏移问题

### 问题分析
当前窗口缩放存在鼠标位置偏移问题。Gemini 建议使用**增量法（Delta）**：
- 不管鼠标具体在哪，只管**鼠标移动了多少距离**
- 公式：`新尺寸 = 初始尺寸 + (当前鼠标位置 - 初始鼠标位置)`

### 优势
1. **无视层级**：不管在哪个控件上触发事件，`x_root` 是屏幕绝对坐标，差值永远准确
2. **跟手性好**：鼠标往右移 10 像素，窗口就变宽 10 像素，完全线性对应

### 修改步骤

#### 步骤 1: 重写 `on_resize_start` 方法
使用新的变量名记录初始状态：
```python
def on_resize_start(self, event):
    """开始缩放：记录初始状态"""
    self.is_resizing = True
    self.resize_start_mouse_x = event.x_root
    self.resize_start_mouse_y = event.y_root
    self.resize_start_w = self.winfo_width()
    self.resize_start_h = self.winfo_height()
    self.lift()
```

#### 步骤 2: 重写 `on_resize_motion` 方法
使用增量法计算新尺寸：
```python
def on_resize_motion(self, event):
    """缩放中：计算增量并应用"""
    if not self.is_resizing:
        return
    
    delta_x = event.x_root - self.resize_start_mouse_x
    delta_y = event.y_root - self.resize_start_mouse_y
    
    new_width = self.resize_start_w + delta_x
    new_height = self.resize_start_h + delta_y
    
    # 限制最小尺寸
    new_width = max(self.min_width, new_width)
    new_height = max(self.min_height, new_height)
    
    # 边界限制
    if self.master:
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()
        if self.winfo_x() + new_width > parent_w:
            new_width = parent_w - self.winfo_x()
        if self.winfo_y() + new_height > parent_h:
            new_height = parent_h - self.winfo_y()
    
    self.configure(width=new_width, height=new_height)
```

#### 步骤 3: 清理旧的偏移量变量
删除之前添加的 `resize_offset_x` 和 `resize_offset_y` 相关代码。

### 涉及文件
- `main.py`

### 预期效果
- 鼠标往右移 10 像素，窗口就变宽 10 像素
- 完全线性对应，无偏移问题
- 无视点击位置，体验一致

### 归档
- 扫描 `.trae/documents/` 目录
- 调用 AutoArchive Skill 归档文档
- 更新 Changelog