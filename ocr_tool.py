# -*- coding: utf-8 -*-
"""
OCR 工具模块 - 基于 RapidOCR (封装 vision_core.py)
实现文字识别和定位功能，支持中文
"""

import numpy as np
from PIL import Image
from typing import Optional, Tuple, List
import threading
import logging

log_dir = "log"
import os
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'ocr_tool.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ocr_tool')


class OCRTool:
    """
    OCR 工具类，封装 vision_core.py 的 RapidOCR 功能
    
    提供线程安全的文字识别和定位功能
    """
    
    def __init__(self):
        """
        初始化 OCR 工具
        """
        self._lock = threading.Lock()
        self._ocr_engine = None
        self._initialized = False
        logger.info("OCR 工具初始化中...")
    
    def _ensure_initialized(self):
        """
        确保 OCR 引擎已初始化（延迟加载）
        """
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    try:
                        from vision_core import VisionCore
                        # 创建 VisionCore 实例（使用屏幕截图模式）
                        self._vision_core = VisionCore(hwnd=None)
                        # 确保 OCR 引擎初始化
                        self._vision_core._ensure_ocr()
                        self._initialized = True
                        logger.info("OCR 引擎初始化成功")
                    except ImportError:
                        logger.error("vision_core 未找到，请确保项目结构正确")
                        raise
                    except Exception as e:
                        logger.error(f"OCR 引擎初始化失败: {e}")
                        raise
    
    def find_text(self, image: Image.Image, target_text: str, confidence_threshold: float = 0.5) -> Optional[Tuple[int, int, float]]:
        """
        在图像中查找指定文字并返回中心坐标
        
        Args:
            image: PIL 图像对象
            target_text: 要查找的目标文字
            confidence_threshold: 置信度阈值，默认 0.5
        
        Returns:
            如果找到，返回 (x, y, confidence) 元组，其中 (x, y) 是中心像素坐标，confidence 是置信度
            如果未找到，返回 None
        """
        self._ensure_initialized()
        
        with self._lock:
            try:
                # 转换为 numpy 数组
                img_array = np.array(image)
                
                # 如果图像是 RGBA，转换为 RGB
                if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                    img_array = img_array[:, :, :3]
                
                # 调用 OCR
                result, _ = self._vision_core._ocr_engine(img_array)
                
                if not result:
                    logger.debug(f"未识别到任何文字")
                    return None
                
                # 查找匹配的文字
                best_match = None
                best_confidence = 0.0
                
                for item in result:
                    box, (ocr_text, confidence) = item[0], item[1]
                    
                    # 检查是否匹配目标文字
                    if target_text in ocr_text:
                        if confidence > best_confidence and confidence >= confidence_threshold:
                            best_confidence = confidence
                            
                            # 计算中心坐标
                            box_array = np.array(box)
                            center_x = int(np.mean(box_array[:, 0]))
                            center_y = int(np.mean(box_array[:, 1]))
                            
                            best_match = (center_x, center_y, confidence)
                            logger.info(f"找到文字 '{target_text}' (识别为: '{ocr_text}') 坐标: ({center_x}, {center_y}) 置信度: {confidence:.2f}")
                
                if best_match:
                    return best_match
                else:
                    logger.debug(f"未找到文字 '{target_text}' (置信度阈值: {confidence_threshold})")
                    return None
                    
            except Exception as e:
                logger.error(f"OCR 识别失败: {e}")
                return None
    
    def find_all_text(self, image: Image.Image, confidence_threshold: float = 0.5) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
        """
        识别图像中的所有文字
        
        Args:
            image: PIL 图像对象
            confidence_threshold: 置信度阈值，默认 0.5
        
        Returns:
            文字列表，每个元素为 (text, (x1, y1, x2, y2), confidence) 元组
        """
        self._ensure_initialized()
        
        with self._lock:
            try:
                img_array = np.array(image)
                
                if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                    img_array = img_array[:, :, :3]
                
                result, _ = self._vision_core._ocr_engine(img_array)
                
                if not result:
                    return []
                
                text_list = []
                for item in result:
                    box, (text, confidence) = item[0], item[1]
                    
                    if confidence >= confidence_threshold:
                        box_array = np.array(box)
                        x1, y1 = int(np.min(box_array[:, 0])), int(np.min(box_array[:, 1]))
                        x2, y2 = int(np.max(box_array[:, 0])), int(np.max(box_array[:, 1]))
                        text_list.append((text, (x1, y1, x2, y2), confidence))
                
                return text_list
                
            except Exception as e:
                logger.error(f"OCR 识别失败: {e}")
                return []
    
    def find_text_fuzzy(self, image: Image.Image, target_text: str, confidence_threshold: float = 0.5, fuzzy_threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """
        模糊查找文字（支持部分匹配）
        
        Args:
            image: PIL 图像对象
            target_text: 要查找的目标文字
            confidence_threshold: OCR 置信度阈值，默认 0.5
            fuzzy_threshold: 模糊匹配阈值（0-1），默认 0.8
        
        Returns:
            如果找到，返回 (x, y, confidence) 元组
            如果未找到，返回 None
        """
        self._ensure_initialized()
        
        with self._lock:
            try:
                img_array = np.array(image)
                
                if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                    img_array = img_array[:, :, :3]
                
                result, _ = self._vision_core._ocr_engine(img_array)
                
                if not result:
                    return None
                
                from difflib import SequenceMatcher
                
                best_match = None
                best_similarity = 0.0
                
                for item in result:
                    box, (text, confidence) = item[0], item[1]
                    
                    if confidence >= confidence_threshold:
                        # 计算相似度
                        similarity = SequenceMatcher(None, target_text, text).ratio()
                        
                        if similarity >= fuzzy_threshold and similarity > best_similarity:
                            best_similarity = similarity
                            
                            box_array = np.array(box)
                            center_x = int(np.mean(box_array[:, 0]))
                            center_y = int(np.mean(box_array[:, 1]))
                            
                            best_match = (center_x, center_y, confidence)
                            logger.info(f"模糊匹配 '{target_text}' (识别为: '{text}') 相似度: {similarity:.2f} 坐标: ({center_x}, {center_y})")
                
                return best_match
                
            except Exception as e:
                logger.error(f"OCR 模糊匹配失败: {e}")
                return None


if __name__ == "__main__":
    print("OCR 工具模块测试")
    print("使用示例:")
    print("""
    from ocr_tool import OCRTool
    from PIL import Image
    
    # 创建 OCR 工具实例
    ocr = OCRTool()
    
    # 加载图像
    image = Image.open("screenshot.png")
    
    # 查找文字
    result = ocr.find_text(image, "开始行动")
    if result:
        x, y, confidence = result
        print(f"找到文字，坐标: ({x}, {y}), 置信度: {confidence}")
    """)
