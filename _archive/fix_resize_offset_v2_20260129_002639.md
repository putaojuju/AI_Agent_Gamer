## 问题分析

鼠标位置和实际拉伸位置仍有偏移。

## 真正原因

事件绑定在 `self` 和 `self.content_frame` 上：
- `self` 是 DraggableWindow (CTkFrame)
- `self.content_frame` 是内部的子 Frame，有 `padx=5, pady=5`
- 当事件在 `content_frame` 上触发时，`event.x_root/y` 是屏幕坐标
- 但 `self.winfo_rootx/y()` 获取的是 `self` 的位置
- 由于 `content_frame` 有内边距，造成偏移

## 解决方案

在 `on_resize_start` 时记录鼠标相对于窗口的偏移量，然后在 `on_resize_motion` 时考虑这个偏移。

```python
def on_resize_start(self, event):
    # ...原有代码...
    # 记录鼠标相对于窗口的偏移
    self.resize_offset_x = event.x_root - self.winfo_rootx()
    self.resize_offset_y = event.y_root - self.winfo_rooty()

def on_resize_motion(self, event):
    # ...
    # 计算新尺寸时考虑偏移
    new_width = max(self.min_width, event.x_root - self.winfo_rootx() - self.resize_offset_x + self.start_width)
    new_height = max(self.min_height, event.y_root - self.winfo_rooty() - self.resize_offset_y + self.start_height)
```

## 修改步骤

### 步骤 1: 修改 `on_resize_start` 方法
添加记录鼠标相对于窗口的偏移量。

### 步骤 2: 修改 `on_resize_motion` 方法
在计算新尺寸时考虑偏移量。

### 涉及文件
- `main.py`

### 预期效果
- 无论点击窗口哪个位置开始拖拽，窗口右下角都能精确跟随鼠标