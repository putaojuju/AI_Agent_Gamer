# -*- coding: utf-8 -*-
"""
ScriptManager启动脚本
确保在虚拟环境中运行ScriptManager，支持命令行参数
"""

import os
import sys
import subprocess
import argparse


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"当前Python版本：{version.major}.{version.minor}.{version.micro}")
    
    # Python 3.13+ 可能与某些依赖不兼容
    if version.major == 3 and version.minor >= 13:
        print("警告：Python 3.13+ 版本可能与某些依赖存在兼容性问题")
        print("建议使用 Python 3.9-3.12 版本以获得最佳兼容性")
    return version


def check_dependencies():
    """检查关键依赖"""
    required_deps = [
        "numpy",
        "airtest",
        "psutil",
        "pywin32",
        "cv2",  # opencv-python
    ]
    
    print("检查关键依赖...")
    missing_deps = []
    for dep in required_deps:
        try:
            if dep == "cv2":
                __import__("cv2")
            else:
                __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"缺少依赖：{', '.join(missing_deps)}")
        print("建议运行：venv\\Scripts\\pip install -r requirements.txt")
    
    return missing_deps


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ScriptManager启动脚本')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--no-venv', action='store_true', help='不使用虚拟环境')
    parser.add_argument('--ignore-deps', action='store_true', help='忽略依赖检查')
    args = parser.parse_args()
    
    print("="*50)
    print("ScriptManager 启动脚本")
    print("="*50)
    
    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 脚本管理器主文件
    manager_script = os.path.join(project_root, 'script_manager.py')
    
    # 检查脚本是否存在
    if not os.path.exists(manager_script):
        print(f"错误：脚本管理器文件不存在：{manager_script}")
        sys.exit(1)
    
    if args.no_venv:
        # 不使用虚拟环境，直接运行
        print("使用当前Python解释器运行ScriptManager...")
        check_python_version()
        if not args.ignore_deps:
            missing_deps = check_dependencies()
            if missing_deps:
                response = input("缺少依赖，是否继续运行？(y/n): ")
                if response.lower() != 'y':
                    sys.exit(0)
        cmd = [sys.executable, manager_script]
        if args.debug:
            cmd.append('--debug')
        subprocess.run(cmd)
    else:
        # 检查虚拟环境是否存在
        venv_path = os.path.join(project_root, 'venv')
        venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            print(f"使用虚拟环境运行ScriptManager：{venv_python}")
            
            # 检查虚拟环境Python版本
            venv_version = subprocess.check_output([venv_python, '--version'], 
                                                 text=True).strip()
            print(f"虚拟环境Python版本：{venv_version}")
            
            # 检查虚拟环境中的依赖
            if not args.ignore_deps:
                print("检查虚拟环境依赖...")
                # 创建临时检查脚本
                check_script_content = r"""
import sys
import os

# 添加虚拟环境site-packages到path
sys.path.insert(0, '{venv_path}/Lib/site-packages')

# 检查关键依赖
required_deps = ["numpy", "airtest", "psutil", "win32gui", "cv2"]

print("检查关键依赖...")
missing_deps = []
for dep in required_deps:
    try:
        __import__(dep)
        print("[OK] " + dep + " 已安装")
    except ImportError as e:
        print("[ERROR] " + dep + " 未安装: " + str(e))
        missing_deps.append(dep)

if missing_deps:
    print("缺少依赖：" + ", ".join(missing_deps))
    print(r"建议运行：venv\Scripts\pip install -r requirements.txt")
else:
    print("所有依赖已安装")
"""

                # 替换虚拟环境路径，确保路径中的反斜杠被正确处理
                # 将路径转换为原始字符串格式，避免转义序列问题
                venv_path_escaped = venv_path.replace('\\', '\\\\')
                check_script_content = check_script_content.replace('{venv_path}', venv_path_escaped)
                
                # 写入临时检查脚本
                temp_script = os.path.join(project_root, 'temp_dep_check.py')
                with open(temp_script, 'w', encoding='utf-8') as f:
                    f.write(check_script_content)
                
                # 运行临时检查脚本
                check_cmd = [venv_python, temp_script]
                subprocess.run(check_cmd)
                
                # 删除临时检查脚本
                os.remove(temp_script)
            
            # 使用虚拟环境的Python解释器运行脚本
            cmd = [venv_python, manager_script]
            if args.debug:
                cmd.append('--debug')
            subprocess.run(cmd)
        else:
            print("警告：未检测到虚拟环境，将使用当前Python解释器运行")
            print("建议运行：python -m venv venv && venv\\Scripts\\pip install -r requirements.txt")
            
            # 确认是否继续
            response = input("是否继续运行？(y/n): ")
            if response.lower() == 'y':
                check_python_version()
                if not args.ignore_deps:
                    missing_deps = check_dependencies()
                    if missing_deps:
                        response = input("缺少依赖，是否继续运行？(y/n): ")
                        if response.lower() != 'y':
                            sys.exit(0)
                cmd = [sys.executable, manager_script]
                if args.debug:
                    cmd.append('--debug')
                subprocess.run(cmd)
            else:
                sys.exit(0)


if __name__ == "__main__":
    main()