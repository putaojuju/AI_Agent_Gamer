## 执行计划：集成 Performance Monitor 到主程序

### 目标
将 performance_monitor.py 集成到 main.py 中，启用性能监控功能。

### 修改步骤

#### 步骤 1: 在 main.py 中导入性能监控模块
在导入部分添加：
```python
from performance_monitor import performance_monitor
```

#### 步骤 2: 在 AICmdCenter 类初始化时启动监控
在 `__init__` 方法中：
```python
# 启动性能监控
performance_monitor.start_monitoring()
self.add_log("性能监控已启动", type="SYSTEM")
```

#### 步骤 3: 在关键操作处添加性能记录

**截图操作** - 在 `test_snapshot` 方法中：
```python
start_time = time.time()
img = self.game_window_driver.snapshot()
performance_monitor.record_snapshot(time.time() - start_time)
```

**智能代理循环** - 在 `process_ui_queue` 或代理相关方法中记录操作耗时。

#### 步骤 4: 在程序关闭时停止监控并生成报告
在 `on_closing` 方法中：
```python
# 停止性能监控并生成报告
report = performance_monitor.stop_monitoring()
if report:
    self.add_log("性能监控报告已生成", detail=report[:500], type="SYSTEM")
```

#### 步骤 5: 添加性能监控菜单或按钮（可选）
在 UI 中添加查看实时性能数据的入口。

### 涉及文件
- `main.py` - 主程序入口

### 验证
1. 启动程序后检查 log/performance_monitor.log 是否有记录
2. 执行截图操作后检查是否有性能数据
3. 关闭程序时检查是否生成完整报告

### 归档
- 扫描 `.trae/documents/` 目录
- 调用 AutoArchive Skill 归档文档
- 更新 Changelog