## 问题分析

鼠标位置和实际拉伸位置有偏移。

## 原因

当前的缩放逻辑是基于鼠标移动的距离（delta）来调整窗口大小：
```python
delta_x = event.x_root - self.start_x
new_width = start_width + delta_x
```

这种方式的问题是：
1. 用户点击窗口任意位置开始拖拽
2. 窗口大小增加量 = 鼠标移动距离
3. 但用户期望的是：窗口右下角跟随鼠标位置

## 解决方案

改为基于鼠标当前位置与窗口左上角位置的关系来计算新尺寸：

```python
# 新宽度 = 鼠标屏幕X - 窗口左上角X
new_width = event.x_root - self.winfo_rootx()
# 新高度 = 鼠标屏幕Y - 窗口左上角Y  
new_height = event.y_root - self.winfo_rooty()
```

这样窗口右下角会精确跟随鼠标位置。

## 修改步骤

### 步骤 1: 修改 `on_resize_motion` 方法
替换原有的 delta 计算方式，改为直接基于鼠标位置计算。

### 涉及文件
- `main.py`

### 预期效果
- 窗口右下角精确跟随鼠标位置
- 无偏移问题