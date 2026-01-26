import os
import time
from typing import Optional, Dict, Any

class Logger:
    """
    日志记录器类
    实现持久化存储功能，每次运行自动在 logs/ 目录下生成按日期命名的日志文件
    """
    def __init__(self):
        self.log_file = None
        self.log_file_path = None
        self._initialize_log()
    
    def _initialize_log(self):
        """
        初始化日志系统
        检查 logs/ 目录是否存在，创建按日期命名的日志文件
        """
        try:
            # 确保 logs/ 目录存在
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 生成日志文件名：session_YYYY-MM-DD_HH-MM-SS.log
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            self.log_file_path = os.path.join(log_dir, f"session_{timestamp}.log")
            
            try:
                # 打开日志文件，使用追加模式
                self.log_file = open(self.log_file_path, "a", encoding="utf-8")
            except Exception as e:
                print(f"无法创建日志文件: {e}")
                self.log_file = None
        except Exception as e:
            print(f"初始化日志系统失败: {e}")
            self.log_file = None
    
    def write(self, message: Dict[str, Any]):
        """
        写入日志消息
        
        Args:
            message: 日志消息字典，包含 title, type, detail 等字段
        """
        if not self.log_file:
            return
        
        try:
            # 获取时间戳
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 提取消息字段
            msg_type = message.get("type", "SYSTEM").upper()
            title = message.get("title", message.get("text", "Info"))
            detail = message.get("detail", "")
            
            # 构建日志行
            log_line = f"[{timestamp}] [{msg_type}] {title}"
            if detail:
                log_line += f" | Detail: {detail}"
            log_line += "\n"
            
            # 写入文件
            self.log_file.write(log_line)
            self.log_file.flush()  # 立即刷新，确保数据写入
        except Exception as e:
            print(f"写入日志失败: {e}")
    
    def close(self):
        """
        关闭日志文件
        """
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
    
    def get_log_file_path(self) -> Optional[str]:
        """
        获取当前日志文件路径
        
        Returns:
            日志文件路径，如果未初始化则返回 None
        """
        return self.log_file_path

# 创建全局日志实例
logger = Logger()

# 导出函数供其他模块使用
def get_logger() -> Logger:
    """
    获取日志记录器实例
    
    Returns:
        Logger 实例
    """
    return logger

def write_log(message: Dict[str, Any]):
    """
    写入日志消息的便捷函数
    
    Args:
        message: 日志消息字典
    """
    logger.write(message)
