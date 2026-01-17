# -*- coding: utf-8 -*-
"""
性能监控模块
用于监控脚本运行时的性能指标，包括CPU、内存、截图耗时等
"""

import time
import psutil
import logging
from collections import deque
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('performance_monitor')

class PerformanceMonitor:
    """
    性能监控器
    监控脚本运行时的性能指标
    """
    
    def __init__(self, max_history=100):
        """
        初始化性能监控器
        Args:
            max_history: 保留的历史记录数量
        """
        self.max_history = max_history
        self.start_time = None
        self.snapshot_times = deque(maxlen=max_history)
        self.touch_times = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        self.cpu_usage = deque(maxlen=max_history)
        self.snapshot_count = 0
        self.touch_count = 0
        self.error_count = 0
        self.warning_count = 0
        
        logger.info("性能监控器已初始化")
    
    def start_monitoring(self):
        """
        开始监控
        """
        self.start_time = time.time()
        logger.info(f"开始性能监控，时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop_monitoring(self):
        """
        停止监控并生成报告
        """
        if not self.start_time:
            logger.warning("性能监控未启动")
            return
        
        end_time = time.time()
        total_time = end_time - self.start_time
        
        # 生成性能报告
        report = self.generate_report(total_time)
        logger.info(f"性能监控结束，总运行时间：{total_time:.2f}秒")
        logger.info(f"性能报告：\n{report}")
        
        return report
    
    def record_snapshot(self, duration):
        """
        记录截图操作
        Args:
            duration: 截图耗时（秒）
        """
        self.snapshot_count += 1
        self.snapshot_times.append(duration)
        
        # 记录当前资源使用情况
        self._record_resource_usage()
        
        logger.debug(f"截图操作 #{self.snapshot_count}，耗时：{duration:.3f}秒")
    
    def record_touch(self, duration):
        """
        记录点击操作
        Args:
            duration: 点击耗时（秒）
        """
        self.touch_count += 1
        self.touch_times.append(duration)
        
        logger.debug(f"点击操作 #{self.touch_count}，耗时：{duration:.3f}秒")
    
    def record_error(self, error_type, message):
        """
        记录错误
        Args:
            error_type: 错误类型
            message: 错误信息
        """
        self.error_count += 1
        logger.error(f"错误 #{self.error_count} - {error_type}: {message}")
    
    def record_warning(self, warning_type, message):
        """
        记录警告
        Args:
            warning_type: 警告类型
            message: 警告信息
        """
        self.warning_count += 1
        logger.warning(f"警告 #{self.warning_count} - {warning_type}: {message}")
    
    def _record_resource_usage(self):
        """
        记录当前资源使用情况
        """
        try:
            # 获取当前进程
            process = psutil.Process()
            
            # 获取内存使用情况（MB）
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
            
            # 获取CPU使用情况（百分比）
            cpu_percent = process.cpu_percent(interval=0.1)
            self.cpu_usage.append(cpu_percent)
            
            logger.debug(f"资源使用 - CPU: {cpu_percent:.1f}%, 内存: {memory_mb:.1f}MB")
            
        except Exception as e:
            logger.error(f"记录资源使用情况失败：{e}")
    
    def get_average_snapshot_time(self):
        """
        获取平均截图时间
        Returns:
            float: 平均截图时间（秒）
        """
        if not self.snapshot_times:
            return 0.0
        return sum(self.snapshot_times) / len(self.snapshot_times)
    
    def get_average_touch_time(self):
        """
        获取平均点击时间
        Returns:
            float: 平均点击时间（秒）
        """
        if not self.touch_times:
            return 0.0
        return sum(self.touch_times) / len(self.touch_times)
    
    def get_average_memory_usage(self):
        """
        获取平均内存使用量
        Returns:
            float: 平均内存使用量（MB）
        """
        if not self.memory_usage:
            return 0.0
        return sum(self.memory_usage) / len(self.memory_usage)
    
    def get_average_cpu_usage(self):
        """
        获取平均CPU使用率
        Returns:
            float: 平均CPU使用率（百分比）
        """
        if not self.cpu_usage:
            return 0.0
        return sum(self.cpu_usage) / len(self.cpu_usage)
    
    def generate_report(self, total_time):
        """
        生成性能报告
        Args:
            total_time: 总运行时间（秒）
        Returns:
            str: 性能报告文本
        """
        report_lines = [
            "=" * 60,
            "性能监控报告",
            "=" * 60,
            f"开始时间：{datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}",
            f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总运行时间：{total_time:.2f}秒 ({total_time/60:.2f}分钟)",
            "",
            "操作统计：",
            f"  截图次数：{self.snapshot_count}",
            f"  点击次数：{self.touch_count}",
            f"  错误次数：{self.error_count}",
            f"  警告次数：{self.warning_count}",
            "",
            "性能指标：",
            f"  平均截图时间：{self.get_average_snapshot_time():.3f}秒",
            f"  平均点击时间：{self.get_average_touch_time():.3f}秒",
            f"  平均内存使用：{self.get_average_memory_usage():.1f}MB",
            f"  平均CPU使用率：{self.get_average_cpu_usage():.1f}%",
            "",
            "性能评分：",
            f"  截图性能：{self._calculate_snapshot_performance()}",
            f"  点击性能：{self._calculate_touch_performance()}",
            f"  资源效率：{self._calculate_resource_efficiency(total_time)}",
            f"  综合评分：{self._calculate_overall_score(total_time)}",
            "=" * 60
        ]
        
        return "\n".join(report_lines)
    
    def _calculate_snapshot_performance(self):
        """
        计算截图性能评分
        Returns:
            str: 性能评分
        """
        avg_time = self.get_average_snapshot_time()
        if avg_time <= 0.5:
            return "优秀 (<=0.5秒)"
        elif avg_time <= 1.0:
            return "良好 (0.5-1.0秒)"
        elif avg_time <= 2.0:
            return "一般 (1.0-2.0秒)"
        else:
            return "较差 (>2.0秒)"
    
    def _calculate_touch_performance(self):
        """
        计算点击性能评分
        Returns:
            str: 性能评分
        """
        avg_time = self.get_average_touch_time()
        if avg_time <= 0.1:
            return "优秀 (<=0.1秒)"
        elif avg_time <= 0.2:
            return "良好 (0.1-0.2秒)"
        elif avg_time <= 0.5:
            return "一般 (0.2-0.5秒)"
        else:
            return "较差 (>0.5秒)"
    
    def _calculate_resource_efficiency(self, total_time):
        """
        计算资源效率评分
        Args:
            total_time: 总运行时间（秒）
        Returns:
            str: 资源效率评分
        """
        avg_memory = self.get_average_memory_usage()
        avg_cpu = self.get_average_cpu_usage()
        
        # 计算资源效率指数（越低越好）
        efficiency_index = (avg_memory * avg_cpu) / (total_time + 1)
        
        if efficiency_index <= 10:
            return "优秀 (高效)"
        elif efficiency_index <= 50:
            return "良好 (较高效)"
        elif efficiency_index <= 100:
            return "一般 (中等)"
        else:
            return "较差 (低效)"
    
    def _calculate_overall_score(self, total_time):
        """
        计算综合评分
        Args:
            total_time: 总运行时间（秒）
        Returns:
            str: 综合评分
        """
        # 基于错误率计算稳定性得分
        total_operations = self.snapshot_count + self.touch_count
        error_rate = self.error_count / (total_operations + 1) if total_operations > 0 else 0
        stability_score = max(0, 100 - error_rate * 100)
        
        # 基于资源使用计算效率得分
        avg_memory = self.get_average_memory_usage()
        avg_cpu = self.get_average_cpu_usage()
        resource_score = max(0, 100 - (avg_memory / 100 + avg_cpu))
        
        # 综合得分
        overall_score = (stability_score + resource_score) / 2
        
        if overall_score >= 80:
            return f"优秀 ({overall_score:.1f}/100)"
        elif overall_score >= 60:
            return f"良好 ({overall_score:.1f}/100)"
        elif overall_score >= 40:
            return f"一般 ({overall_score:.1f}/100)"
        else:
            return f"较差 ({overall_score:.1f}/100)"

# 单例模式
performance_monitor = PerformanceMonitor()

# 测试代码
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # 模拟一些操作
    for i in range(5):
        start = time.time()
        time.sleep(0.1)
        monitor.record_snapshot(time.time() - start)
        
        start = time.time()
        time.sleep(0.05)
        monitor.record_touch(time.time() - start)
    
    # 模拟错误和警告
    monitor.record_error("测试错误", "这是一个测试错误")
    monitor.record_warning("测试警告", "这是一个测试警告")
    
    # 停止监控并生成报告
    report = monitor.stop_monitoring()
    print(report)
