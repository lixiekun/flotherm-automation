#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FloTHERM GUI 自动化操作脚本

使用 PyAutoGUI 模拟鼠标点击和键盘操作，实现 FloTHERM 自动化。

安装依赖:
    pip install pyautogui pillow opencv-python

使用方法:
    python gui_automation.py --macro model.xml
    python gui_automation.py --open model.pack --solve --save result.pack
    python gui_automation.py --record  # 录制鼠标位置
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

try:
    import pyautogui
    # 安全设置：鼠标移到角落可中断
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5  # 每个操作后暂停 0.5 秒
except ImportError:
    print("❌ 请先安装 pyautogui: pip install pyautogui pillow")
    sys.exit(1)


class FloTHERMAutomation:
    """FloTHERM GUI 自动化操作类"""

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._find_flotherm()
        self.screen_width, self.screen_height = pyautogui.size()
        self.images_dir = Path(__file__).parent / "gui_images"

        print(f"📐 屏幕分辨率: {self.screen_width}x{self.screen_height}")
        print(f"📁 FloTHERM: {self.flotherm_path}")

    def _find_flotherm(self) -> str:
        """查找 FloTHERM 可执行文件"""
        possible_paths = [
            r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
            r"C:\Program Files\Siemens\SimcenterFlotherm\2021.1\bin\flotherm.exe",
            r"C:\Program Files\Siemens\SimcenterFlotherm\2022.1\bin\flotherm.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def launch(self, wait_time: int = 10):
        """启动 FloTHERM"""
        if not self.flotherm_path:
            raise FileNotFoundError("未找到 FloTHERM，请手动指定路径")

        print(f"🚀 启动 FloTHERM...")
        subprocess.Popen([self.flotherm_path])
        print(f"⏳ 等待 {wait_time} 秒...")
        time.sleep(wait_time)
        print("✅ FloTHERM 已启动")

    def click_image(self, image_name: str, timeout: int = 10) -> bool:
        """通过图像识别点击"""
        image_path = self.images_dir / f"{image_name}.png"
        if not image_path.exists():
            print(f"❌ 图像文件不存在: {image_path}")
            return False

        print(f"🔍 查找图像: {image_name}...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateOnScreen(str(image_path), confidence=0.8)
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center)
                    print(f"✅ 点击: {image_name} at ({center.x}, {center.y})")
                    return True
            except Exception:
                pass
            time.sleep(0.5)

        print(f"❌ 未找到图像: {image_name}")
        return False

    def click_position(self, x: int, y: int):
        """点击指定坐标"""
        pyautogui.click(x, y)
        print(f"👆 点击坐标: ({x}, {y})")

    def type_text(self, text: str):
        """输入文字"""
        pyautogui.write(text)
        print(f"⌨️ 输入: {text}")

    def press_key(self, key: str):
        """按键"""
        pyautogui.press(key)
        print(f"按键: {key}")

    def hotkey(self, *keys):
        """组合键"""
        pyautogui.hotkey(*keys)
        print(f"组合键: {'+'.join(keys)}")

    def open_file(self, filepath: str):
        """打开文件 (Ctrl+O)"""
        print(f"📂 打开文件: {filepath}")
        self.hotkey('ctrl', 'o')
        time.sleep(1)
        self.type_text(filepath)
        self.press_key('enter')

    def save_file(self, filepath: str):
        """保存文件 (Ctrl+S)"""
        print(f"💾 保存文件: {filepath}")
        self.hotkey('ctrl', 's')
        time.sleep(0.5)
        self.type_text(filepath)
        self.press_key('enter')

    def run_macro(self, macro_path: str):
        """
        运行宏文件
        菜单路径: Tools -> Macro -> Play
        """
        print(f"▶️ 运行宏: {macro_path}")

        # 方法1: 使用快捷键（如果 FloTHERM 支持）
        # self.hotkey('alt', 't')  # Tools 菜单

        # 方法2: 点击菜单
        # 需要预先准备好菜单截图
        if self.click_image("menu_tools"):
            time.sleep(0.5)
            if self.click_image("menu_macro"):
                time.sleep(0.3)
                if self.click_image("menu_play"):
                    time.sleep(1)
                    # 输入宏文件路径
                    self.type_text(macro_path)
                    self.press_key('enter')
                    print("✅ 宏已执行")

    def solve(self):
        """执行求解 (需要根据实际界面调整)"""
        print("⚙️ 执行求解...")
        # 方法1: 快捷键
        # self.hotkey('ctrl', 's')  # 或其他快捷键

        # 方法2: 点击求解按钮
        self.click_image("button_solve", timeout=300)  # 求解可能需要较长时间

    def wait_for_solve(self, timeout: int = 3600):
        """等待求解完成"""
        print(f"⏳ 等待求解完成 (最长 {timeout} 秒)...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检测求解完成的标志（需要准备截图）
            if self.click_image("solve_complete", timeout=1):
                print("✅ 求解完成")
                return True
            time.sleep(5)

        print("⏰ 等待超时")
        return False


def record_positions():
    """录制鼠标位置工具"""
    print("\n📍 鼠标位置录制工具")
    print("=" * 50)
    print("将鼠标移到目标位置，按 Enter 记录坐标")
    print("输入 'q' 退出")
    print("=" * 50)

    positions = []
    while True:
        user_input = input("\n按 Enter 记录位置 (q 退出): ").strip()
        if user_input.lower() == 'q':
            break

        x, y = pyautogui.position()
        print(f"  📍 位置: ({x}, {y})")
        positions.append((x, y))

    print("\n📋 录制的位置:")
    for i, (x, y) in enumerate(positions, 1):
        print(f"  {i}. ({x}, {y})")

    return positions


def capture_region():
    """截图工具"""
    print("\n📷 截图工具")
    print("=" * 50)
    print("1. 将鼠标移到截图区域左上角，按 Enter")
    print("2. 将鼠标移到截图区域右下角，按 Enter")
    print("=" * 50)

    input("移到左上角后按 Enter...")
    x1, y1 = pyautogui.position()
    print(f"  左上角: ({x1}, {y1})")

    input("移到右下角后按 Enter...")
    x2, y2 = pyautogui.position()
    print(f"  右下角: ({x2}, {y2})")

    # 截图
    width = x2 - x1
    height = y2 - y1
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))

    # 保存
    images_dir = Path(__file__).parent / "gui_images"
    images_dir.mkdir(exist_ok=True)

    filename = input("文件名 (不含扩展名): ").strip() or "capture"
    save_path = images_dir / f"{filename}.png"
    screenshot.save(save_path)

    print(f"✅ 已保存: {save_path}")


def main():
    parser = argparse.ArgumentParser(
        description="FloTHERM GUI 自动化操作脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 运行宏
    python gui_automation.py --macro model.xml

    # 打开文件、求解、保存
    python gui_automation.py --open model.pack --solve --save result.pack

    # 录制鼠标位置
    python gui_automation.py --record

    # 截图（准备图像识别素材）
    python gui_automation.py --capture
        """
    )

    parser.add_argument("--flotherm", help="FloTHERM 可执行文件路径")
    parser.add_argument("--open", metavar="FILE", help="打开文件")
    parser.add_argument("--macro", metavar="FILE", help="运行宏文件")
    parser.add_argument("--solve", action="store_true", help="执行求解")
    parser.add_argument("--save", metavar="FILE", help="保存文件")
    parser.add_argument("--launch", action="store_true", help="启动 FloTHERM")
    parser.add_argument("--record", action="store_true", help="录制鼠标位置")
    parser.add_argument("--capture", action="store_true", help="截图工具")
    parser.add_argument("--wait", type=int, default=10, help="等待时间（秒）")

    args = parser.parse_args()

    # 录制模式
    if args.record:
        record_positions()
        return

    # 截图模式
    if args.capture:
        capture_region()
        return

    # 自动化操作
    auto = FloTHERMAutomation(args.flotherm)

    # 启动
    if args.launch:
        auto.launch(args.wait)

    # 打开文件
    if args.open:
        auto.open_file(args.open)

    # 运行宏
    if args.macro:
        auto.run_macro(args.macro)

    # 求解
    if args.solve:
        auto.solve()

    # 保存
    if args.save:
        auto.save_file(args.save)

    print("\n✅ 操作完成")


if __name__ == "__main__":
    main()
