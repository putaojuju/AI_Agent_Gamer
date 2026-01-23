# -*- coding: utf-8 -*-
"""
视觉核心模块 - RapidOCR + SoM (Set-of-Mark)
提供截图、OCR识别和网格标注功能
"""

import base64
import io
import numpy as np
import win32gui
import win32con
import win32ui
import mss
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, List
import logging

log_dir = "log"
import os
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'vision_core.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vision_core')


class VisionCore:
    """
    视觉核心类，整合截图、OCR 和网格标注功能
    """
    
    def __init__(self, hwnd: Optional[int] = None, grid_size: int = 4):
        """
        初始化视觉核心
        
        Args:
            hwnd: 目标窗口句柄，如果为 None 则截取主屏幕
            grid_size: 网格大小，默认 4x4
        """
        self.hwnd = hwnd
        self.grid_size = grid_size
        self._ocr_engine = None
        self._ocr_initialized = False
        logger.info(f"视觉核心初始化完成，网格大小: {grid_size}x{grid_size}")
    
    def _ensure_ocr(self):
        """
        确保 OCR 引擎已初始化（延迟加载）
        """
        if not self._ocr_initialized:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._ocr_engine = RapidOCR()
                self._ocr_initialized = True
                logger.info("OCR 引擎初始化成功")
            except ImportError:
                logger.error("rapidocr_onnxruntime 未安装，请运行: pip install rapidocr_onnxruntime")
                raise
            except Exception as e:
                logger.error(f"OCR 引擎初始化失败: {e}")
                raise
    
    def _add_som_grid(self, image: Image.Image) -> Tuple[Image.Image, Dict]:
        """
        在图像上添加 SoM (Set-of-Mark) 网格标注
        
        Args:
            image: PIL 图像对象
        
        Returns:
            (标注后的图像, 网格映射信息)
        """
        img_width, img_height = image.size
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 网格颜色：半透明红色
        grid_color = (255, 0, 0, 80)
        axis_color = (255, 0, 0, 150)
        
        # 绘制垂直线
        for i in range(1, self.grid_size):
            x = int(img_width * i / self.grid_size)
            draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)
        
        # 绘制水平线
        for i in range(1, self.grid_size):
            y = int(img_height * i / self.grid_size)
            draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)
        
        # 绘制坐标轴（左上角）
        axis_length = min(img_width, img_height) // 10
        draw.line([(0, 0), (axis_length, 0)], fill=axis_color, width=2)
        draw.line([(0, 0), (0, axis_length)], fill=axis_color, width=2)
        
        # 添加坐标标记
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((5, 5), "X", fill=axis_color, font=font)
        draw.text((5, 15), "Y", fill=axis_color, font=font)
        
        # 生成网格映射信息
        grid_map = {
            'size': self.grid_size,
            'width': img_width,
            'height': img_height,
            'cells': []
        }
        
        cell_width = img_width / self.grid_size
        cell_height = img_height / self.grid_size
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x1 = int(col * cell_width)
                y1 = int(row * cell_height)
                x2 = int((col + 1) * cell_width)
                y2 = int((row + 1) * cell_height)
                
                grid_map['cells'].append({
                    'row': row,
                    'col': col,
                    'bbox': (x1, y1, x2, y2),
                    'center': (int((x1 + x2) / 2), int((y1 + y2) / 2))
                })
        
        return image, grid_map
    
    def _image_to_base64(self, image: Image.Image, max_size: int = 1280) -> str:
        """
        将 PIL 图像转换为 Base64 字符串
        
        Args:
            image: PIL 图像对象
            max_size: 最大边长（用于压缩以节省 Token）
        
        Returns:
            Base64 编码的 JPEG 图像字符串
        """
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def capture(self) -> Optional[np.ndarray]:
        """
        截取窗口或屏幕
        
        Returns:
            numpy 数组格式的图像 (BGR)，失败返回 None
        """
        try:
            if self.hwnd:
                return self._capture_window()
            else:
                return self._capture_screen()
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def _capture_window(self) -> Optional[np.ndarray]:
        """
        截取指定窗口
        """
        try:
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
            
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            result = win32gui.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 2)
            if result == 0:
                result = win32gui.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 0)
            
            if result == 0:
                logger.error("PrintWindow API 调用失败")
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwndDC)
                return None
            
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)
            
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)
            
            img = img[..., :3]
            img = img[..., ::-1]
            
            return img
            
        except Exception as e:
            logger.error(f"窗口截图失败: {e}")
            return None
    
    def _capture_screen(self) -> Optional[np.ndarray]:
        """
        截取主屏幕
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                screen = np.array(sct_img)
                if screen.shape[-1] >= 3:
                    screen = screen[..., :3]
                return screen
        except Exception as e:
            logger.error(f"屏幕截图失败: {e}")
            return None
    
    def get_annotated_screenshot(self, use_grid: bool = True) -> Optional[Tuple[str, Image.Image, Dict]]:
        """
        获取标注后的截图
        
        Args:
            use_grid: 是否添加网格标注，默认 True
        
        Returns:
            (Base64图片, 原始PIL图片, 网格映射信息)，失败返回 None
        """
        try:
            # 截图
            screenshot_array = self.capture()
            if screenshot_array is None:
                return None
            
            # 转换为 PIL 图像
            image = Image.fromarray(screenshot_array)
            
            # 添加网格标注
            grid_map = {}
            if use_grid:
                image, grid_map = self._add_som_grid(image)
            
            # 转换为 Base64
            base64_img = self._image_to_base64(image)
            
            return base64_img, image, grid_map
            
        except Exception as e:
            logger.error(f"获取标注截图失败: {e}")
            return None
    
    def find_text(self, text: str, confidence_threshold: float = 0.5) -> Optional[Tuple[int, int, float]]:
        """
        在当前截图中查找指定文字
        
        Args:
            text: 要查找的文字
            confidence_threshold: 置信度阈值，默认 0.5
        
        Returns:
            (x, y, confidence) 像素坐标，未找到返回 None
        """
        self._ensure_ocr()
        
        try:
            screenshot_array = self.capture()
            if screenshot_array is None:
                return None
            
            # 转换为 PIL 图像
            image = Image.fromarray(screenshot_array)
            
            # 转换为 numpy 数组
            img_array = np.array(image)
            
            if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                img_array = img_array[:, :, :3]
            
            # 调用 OCR
            result, _ = self._ocr_engine(img_array)
            
            if not result:
                return None
            
            # 查找匹配的文字
            best_match = None
            best_confidence = 0.0
            
            for item in result:
                box, (ocr_text, confidence) = item[0], item[1]
                
                if text in ocr_text:
                    if confidence > best_confidence and confidence >= confidence_threshold:
                        best_confidence = confidence
                        box_array = np.array(box)
                        center_x = int(np.mean(box_array[:, 0]))
                        center_y = int(np.mean(box_array[:, 1]))
                        best_match = (center_x, center_y, confidence)
                        logger.info(f"找到文字 '{text}' (识别为: '{ocr_text}') 坐标: ({center_x}, {center_y}) 置信度: {confidence:.2f}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"查找文字失败: {e}")
            return None
    
    def find_all_text(self, confidence_threshold: float = 0.5) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
        """
        识别当前截图中的所有文字
        
        Args:
            confidence_threshold: 置信度阈值，默认 0.5
        
        Returns:
            文字列表，每个元素为 (text, (x1, y1, x2, y2), confidence)
        """
        self._ensure_ocr()
        
        try:
            screenshot_array = self.capture()
            if screenshot_array is None:
                return []
            
            img_array = screenshot_array
            if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                img_array = img_array[:, :, :3]
            
            result, _ = self._ocr_engine(img_array)
            
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
            logger.error(f"识别文字失败: {e}")
            return []


if __name__ == "__main__":
    print("视觉核心模块测试")
    print("使用示例:")
    print("""
    from vision_core import VisionCore
    
    # 创建视觉核心实例
    vision = VisionCore(hwnd=None, grid_size=4)
    
    # 获取标注截图
    base64_img, pil_img, grid_map = vision.get_annotated_screenshot()
    
    # 查找文字
    result = vision.find_text("开始")
    if result:
        x, y, confidence = result
        print(f"找到文字，坐标: ({x}, {y}), 置信度: {confidence}")
    """)
