# -*- coding: utf-8 -*-
"""
游戏脚本启动器
提供友好的用户界面和错误处理
"""

import os
import sys
import subprocess
import time

def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """打印欢迎横幅"""
    clear_screen()
    print("=" * 50)
    print("          游戏自动化脚本启动器")
    print("=" * 50)
    print()

def print_menu():
    """打印菜单"""
    print("请选择要运行的脚本：")
    print("1. 日常任务脚本")
    print("2. 退出")
    print()

def run_daily_script():
    """运行日常任务脚本"""
    print("正在启动日常任务脚本...")
    print("请确保游戏窗口已经打开并处于前台！")
    print("按任意键继续...")
    input()
    
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 日常脚本路径
        daily_script_path = os.path.join(current_dir, "twinkle_starknightsX", "daily", "daily.py")
        
        print(f"正在执行脚本：{daily_script_path}")
        print("脚本运行中...")
        print("按Ctrl+C可以终止脚本")
        print()
        
        # 运行脚本
        result = subprocess.run([sys.executable, daily_script_path], check=True, capture_output=True, text=True)
        
        print("\n脚本执行成功！")
        print("输出信息：")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"\n脚本执行失败！错误码：{e.returncode}")
        print(f"错误信息：{e.stderr}")
    except FileNotFoundError:
        print(f"\n脚本文件未找到：{daily_script_path}")
    except Exception as e:
        print(f"\n发生未知错误：{str(e)}")
    
    print("\n按任意键返回菜单...")
    input()

def main():
    """主函数"""
    while True:
        print_banner()
        print_menu()
        
        choice = input("请输入选项 (1-2): ")
        
        if choice == '1':
            run_daily_script()
        elif choice == '2':
            print("\n感谢使用游戏自动化脚本！")
            time.sleep(1)
            break
        else:
            print("\n无效的选项，请重新输入！")
            time.sleep(1)

if __name__ == "__main__":
    main()
