# env_check.py
import sys
import importlib

print(f"✅ 当前 Python 版本: {sys.version}")

libs = [
    "rapidocr_onnxruntime", "cv2", "PIL", "numpy", 
    "customtkinter", "win32gui", "langchain"
]

print("-" * 30)
for lib in libs:
    try:
        importlib.import_module(lib)
        print(f"✅ {lib} 导入成功")
    except ImportError as e:
        print(f"❌ {lib} 导入失败: {e}")
    except Exception as e:
        print(f"⚠️ {lib} 发生其他错误: {e}")
