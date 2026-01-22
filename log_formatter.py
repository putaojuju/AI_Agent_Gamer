# -*- coding: utf-8 -*-
"""
日志格式化器 - 增强版
解析脚本输出，识别图片路径，生成结构化日志数据
支持中文翻译和图片缩略图显示
"""

import os
import re
from datetime import datetime

class LogFormatter:
    """
    日志格式化器
    解析 Airtest 脚本输出，识别图片路径和操作类型
    """
    
    def __init__(self):
        self.timestamp_format = "%H:%M:%S"
        
        self.noise_patterns = [
            r'\[DEBUG\].*aircv\.utils',
            r'\[DEBUG\].*find_best_result',
            r'\bbrisk\b',
            r'\bsift\b',
            r'\borb\b',
            r'kaze',
            r'akaze'
        ]
        
        self.translation_map = {
            "Try finding": "🔍 正在寻找",
            "match result: None": "❌ 未找到目标",
            "touch": "👆 点击",
            "swipe": "👆 滑动",
            "wait": "⏱️ 等待",
            "sleep": "⏱️ 等待",
            "keyevent": "⌨️ 按键",
            "type": "⌨️ 输入"
        }
    
    def _is_noise(self, line):
        """
        检查是否为噪音日志
        """
        for pattern in self.noise_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _find_image_recursive(self, filename, search_dir):
        """
        递归搜索图片文件
        Args:
            filename: 文件名（不含路径）
            search_dir: 搜索起始目录
        Returns:
            str: 找到的完整路径，未找到返回 None
        """
        if not search_dir or not os.path.exists(search_dir):
            return None
        
        try:
            for root, dirs, files in os.walk(search_dir):
                if filename in files:
                    return os.path.join(root, filename)
        except Exception:
            pass
        
        return None
    
    def _extract_image_path(self, line, script_dir):
        """
        从日志行中提取图片路径
        支持多种格式：Template(r"path"), Template("path"), Template('path'), Template(path)
        使用更宽松的正则表达式和递归搜索
        """
        pattern = r'([a-zA-Z0-9_\\/:\-\.]+\.(?:png|jpg|jpeg))'
        match = re.search(pattern, line, re.IGNORECASE)
        
        if match:
            raw_path = match.group(1).strip("'").strip('"')
            
            if script_dir:
                possible_paths = [
                    raw_path if os.path.isabs(raw_path) else None,
                    os.path.join(script_dir, raw_path),
                    os.path.join(script_dir, raw_path.replace("/", "\\")),
                    os.path.join(script_dir, os.path.basename(raw_path))
                ]
                
                for p in possible_paths:
                    if p and os.path.exists(p):
                        return p
                
                filename = os.path.basename(raw_path)
                found_path = self._find_image_recursive(filename, script_dir)
                if found_path:
                    return found_path
            
            return raw_path
        
        return None
    
    def _extract_confidence(self, line):
        """
        从匹配结果中提取置信度
        """
        match = re.search(r"'confidence':\s*(\d+\.\d+)", line)
        if match:
            return float(match.group(1))
        return None
    
    def _translate_line(self, line):
        """
        翻译日志行中的关键词
        """
        translated = line
        for eng, chi in self.translation_map.items():
            translated = translated.replace(eng, chi)
        return translated
    
    def parse_line(self, line, script_dir=None):
        """
        解析单行日志
        Args:
            line: 原始日志行
            script_dir: 脚本所在目录（用于解析相对路径）
        Returns:
            dict: 结构化日志数据
                {
                    "timestamp": "HH:MM:SS",
                    "type": "SEARCHING" | "SUCCESS" | "ERROR" | "INFO" | "WARNING",
                    "text": "翻译后的中文日志文本",
                    "image_path": "图片的绝对路径 (如果有)",
                    "confidence": "置信度 (如果有)",
                    "raw": "原始日志"
                }
        """
        if not line or not line.strip():
            return None
        
        raw_line = line.strip()
        
        if self._is_noise(raw_line):
            return None
        
        timestamp = datetime.now().strftime(self.timestamp_format)
        
        result = {
            "timestamp": timestamp,
            "type": "INFO",
            "text": raw_line,
            "image_path": None,
            "confidence": None,
            "raw": raw_line
        }
        
        if script_dir and not os.path.isabs(script_dir):
            script_dir = os.path.abspath(script_dir)
        
        image_path = self._extract_image_path(raw_line, script_dir)
        
        if "Try finding" in raw_line:
            result["type"] = "SEARCHING"
            if image_path:
                filename = os.path.basename(image_path)
                result["text"] = f"🔍 正在寻找: {filename}"
                result["image_path"] = image_path
            else:
                result["text"] = "🔍 正在寻找目标图片..."
            return result
        
        if "match result: None" in raw_line:
            result["type"] = "WARNING"
            result["text"] = "❌ 未找到目标，重试中..."
            return result
        
        if "match result" in raw_line.lower():
            confidence = self._extract_confidence(raw_line)
            result["type"] = "SUCCESS"
            if image_path:
                filename = os.path.basename(image_path)
                result["text"] = f"✅ 识别成功: {filename}"
                if confidence is not None:
                    result["text"] += f" (置信度: {confidence:.2f})"
                    result["confidence"] = confidence
                result["image_path"] = image_path
            else:
                result["text"] = "✅ 识别成功"
                if confidence is not None:
                    result["text"] += f" (置信度: {confidence:.2f})"
                    result["confidence"] = confidence
            return result
        
        if "touch" in raw_line.lower():
            result["type"] = "INFO"
            coord_match = re.search(r'touch\(\s*\(?([^)]+)\)', raw_line)
            if coord_match:
                coords = coord_match.group(1)
                result["text"] = f"👆 点击: {coords}"
            else:
                result["text"] = "👆 点击操作"
            return result
        
        if "swipe" in raw_line.lower():
            result["type"] = "INFO"
            result["text"] = "👆 滑动操作"
            return result
        
        if "wait" in raw_line.lower() or "sleep" in raw_line.lower():
            result["type"] = "INFO"
            result["text"] = "⏱️ 等待中..."
            return result
        
        if "keyevent" in raw_line.lower() or "type" in raw_line.lower():
            result["type"] = "INFO"
            result["text"] = "⌨️ 键盘操作"
            return result
        
        if "error" in raw_line.lower() or "fail" in raw_line.lower() or "exception" in raw_line.lower():
            result["type"] = "ERROR"
            result["text"] = f"❌ {self._translate_line(raw_line)}"
            return result
        
        if "warning" in raw_line.lower() or "warn" in raw_line.lower():
            result["type"] = "WARNING"
            result["text"] = f"⚠️  {self._translate_line(raw_line)}"
            return result
        
        if "success" in raw_line.lower() or "complete" in raw_line.lower() or "finish" in raw_line.lower():
            result["type"] = "SUCCESS"
            result["text"] = f"✅ {self._translate_line(raw_line)}"
            return result
        
        return result
    
    def parse_output(self, output_lines, script_dir=None):
        """
        批量解析多行日志
        Args:
            output_lines: 日志行列表
            script_dir: 脚本所在目录
        Returns:
            list: 结构化日志数据列表
        """
        results = []
        for line in output_lines:
            if line and line.strip():
                parsed = self.parse_line(line, script_dir)
                if parsed:
                    results.append(parsed)
        return results


log_formatter = LogFormatter()

if __name__ == "__main__":
    formatter = LogFormatter()
    
    test_lines = [
        'Try finding Template(r"start_button.png", threshold=0.7)',
        '[DEBUG]<airtest.aircv.utils> find_best_result: brisk',
        '[DEBUG]<airtest.core.api> something',
        'match result: None',
        'match result: {"pos": (100, 200), "confidence": 0.95}',
        'touch((100, 200))',
        'wait(1)',
        'Error: Cannot find image',
        'Script completed successfully'
    ]
    
    print("测试日志解析器:")
    print("=" * 60)
    for line in test_lines:
        result = formatter.parse_line(line, "E:\\games\\test")
        if result:
            print(f"原始: {result['raw']}")
            print(f"类型: {result['type']}")
            print(f"文本: {result['text']}")
            print(f"图片: {result.get('image_path', '无')}")
            print(f"置信度: {result.get('confidence', '无')}")
            print("-" * 60)
