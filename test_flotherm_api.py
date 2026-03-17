#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FloTHERM API 可用性测试脚本

用于检测当前系统上 FloTHERM 的各种自动化接口是否可用。
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name, success, message=""):
    """打印测试结果"""
    status = "✅ 可用" if success else "❌ 不可用"
    print(f"  {name}: {status}")
    if message:
        print(f"    └─ {message}")


def test_python_native_api():
    """测试 Python 原生 API 模块"""
    print_header("1. Python 原生 API 模块测试")

    results = []

    # 测试 flotherm 模块
    try:
        import flotherm
        print_result("flotherm 模块", True, f"版本: {getattr(flotherm, '__version__', '未知')}")
        results.append(("flotherm", True))

        # 尝试创建实例
        try:
            ft = flotherm.FloTHERM()
            print_result("  └─ FloTHERM() 实例", True)
        except Exception as e:
            print_result("  └─ FloTHERM() 实例", False, str(e))

    except ImportError as e:
        print_result("flotherm 模块", False, str(e))
        results.append(("flotherm", False))

    # 测试 flotherm_api 模块
    try:
        import flotherm_api
        print_result("flotherm_api 模块", True)
        results.append(("flotherm_api", True))
    except ImportError as e:
        print_result("flotherm_api 模块", False, str(e))
        results.append(("flotherm_api", False))

    # 测试 ftapi 模块
    try:
        from ftapi import FloTHERM
        print_result("ftapi 模块", True)
        results.append(("ftapi", True))
    except ImportError as e:
        print_result("ftapi 模块", False, str(e))
        results.append(("ftapi", False))

    # 测试 pyflotherm 模块
    try:
        import pyflotherm
        print_result("pyflotherm 模块", True)
        results.append(("pyflotherm", True))
    except ImportError as e:
        print_result("pyflotherm 模块", False, str(e))
        results.append(("pyflotherm", False))

    return results


def test_com_api():
    """测试 COM API (Windows only)"""
    print_header("2. COM API 测试 (Windows)")

    if sys.platform != "win32":
        print("  ⚠️ COM API 仅在 Windows 上可用")
        return [("COM API", False, "非 Windows 系统")]

    results = []

    # 检查 pywin32 是否安装
    try:
        import win32com.client
        print_result("pywin32 模块", True)
    except ImportError:
        print_result("pywin32 模块", False, "请运行: pip install pywin32")
        return [("COM API", False, "pywin32 未安装")]

    # 测试不同的 ProgID
    prog_ids = [
        "Flotherm.Application",
        "Flotherm.Application.1",
        "SimcenterFlotherm.Application",
        "MentorFlotherm.Application",
        "FloTHERM.Application",
    ]

    for prog_id in prog_ids:
        try:
            # 尝试获取 COM 对象（不启动）
            import pythoncom
            clsid = pythoncom.MakeIID(prog_id.replace(".", ""))
        except:
            pass

        # 尝试创建实例
        try:
            flotherm = win32com.client.Dispatch(prog_id)
            print_result(f"COM: {prog_id}", True)
            results.append((prog_id, True))

            # 尝试获取版本
            try:
                version = getattr(flotherm, 'Version', '未知')
                print(f"    └─ 版本: {version}")
            except:
                pass

            # 尝试获取可见性属性
            try:
                visible = flotherm.Visible
                print(f"    └─ Visible 属性: {visible}")
            except:
                pass

            break  # 成功则退出循环

        except Exception as e:
            print_result(f"COM: {prog_id}", False)
            results.append((prog_id, False))

    return results


def test_flotherm_installation():
    """检查 FloTHERM 安装目录"""
    print_header("3. FloTHERM 安装目录检查")

    results = []

    # 可能的安装路径
    possible_paths = [
        r"C:\Program Files\Siemens\SimcenterFlotherm",
        r"C:\Program Files\Siemens\Simcenter Flotherm",
        r"C:\Program Files (x86)\Siemens\SimcenterFlotherm",
        r"C:\Program Files\MentorMA",
        r"C:\Program Files (x86)\MentorMA",
        r"C:\Program Files\Mentor Graphics",
        r"C:\Program Files (x86)\Mentor Graphics",
    ]

    found_installations = []

    for base_path in possible_paths:
        if os.path.exists(base_path):
            print(f"\n  📁 找到安装目录: {base_path}")

            # 列出子目录（版本）
            try:
                subdirs = os.listdir(base_path)
                for subdir in subdirs:
                    full_path = os.path.join(base_path, subdir)
                    if os.path.isdir(full_path):
                        print(f"    ├─ {subdir}/")

                        # 检查关键文件
                        check_files = [
                            ("bin/flotherm.exe", "可执行文件"),
                            ("python/", "Python 模块"),
                            ("api/", "API 文档"),
                            ("docs/", "文档"),
                            ("examples/", "示例"),
                            ("examples/FloSCRIPT/", "FloSCRIPT 示例"),
                        ]

                        for file_name, desc in check_files:
                            file_path = os.path.join(full_path, file_name)
                            if os.path.exists(file_path):
                                print(f"    │   ├─ ✅ {desc}: {file_name}")
                                if "python" in file_name.lower() or "api" in file_name.lower():
                                    results.append((f"{subdir}/{file_name}", True))

                        found_installations.append(full_path)
            except Exception as e:
                print(f"    └─ 读取目录失败: {e}")

    if not found_installations:
        print("  ❌ 未找到 FloTHERM 安装目录")
        print("  请手动检查 FloTHERM 是否已安装")

    return results


def test_command_line():
    """测试命令行接口"""
    print_header("4. 命令行接口测试")

    results = []

    if sys.platform == "win32":
        # Windows 下测试
        commands = [
            ("flotherm -h", "flotherm 帮助"),
            ("flotherm --version", "flotherm 版本"),
            ("where flotherm", "flotherm 路径"),
        ]
    else:
        # Linux/Mac 下测试
        commands = [
            ("flotherm -h", "flotherm 帮助"),
            ("which flotherm", "flotherm 路径"),
        ]

    for cmd, desc in commands:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_result(desc, True, result.stdout.strip()[:50])
                results.append((desc, True))
            else:
                print_result(desc, False, result.stderr.strip()[:50] if result.stderr else "命令执行失败")
                results.append((desc, False))
        except subprocess.TimeoutExpired:
            print_result(desc, False, "超时")
            results.append((desc, False))
        except Exception as e:
            print_result(desc, False, str(e))
            results.append((desc, False))

    return results


def test_floscript_examples():
    """检查 FloSCRIPT 示例"""
    print_header("5. FloSCRIPT 示例文件检查")

    results = []

    # 可能的 FloSCRIPT 示例路径
    example_paths = [
        r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\examples\FloSCRIPT",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2021.1\examples\FloSCRIPT",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2021.2\examples\FloSCRIPT",
        r"C:\Program Files (x86)\Siemens\SimcenterFlotherm\2020.2\examples\FloSCRIPT",
        r"C:\Program Files\MentorMA\flosuite_v13\flotherm\examples\FloSCRIPT",
    ]

    found = False
    for path in example_paths:
        if os.path.exists(path):
            found = True
            print(f"\n  📁 找到 FloSCRIPT 示例: {path}")

            try:
                files = os.listdir(path)
                xml_files = [f for f in files if f.endswith('.xml')]

                if xml_files:
                    print(f"  找到 {len(xml_files)} 个 XML 示例文件:")
                    for xml_file in xml_files[:5]:  # 只显示前5个
                        print(f"    ├─ {xml_file}")
                    if len(xml_files) > 5:
                        print(f"    └─ ... 还有 {len(xml_files) - 5} 个文件")
                    results.append(("FloSCRIPT 示例", True))
                else:
                    print("  ⚠️ 目录存在但没有 XML 文件")
                    results.append(("FloSCRIPT 示例", False))
            except Exception as e:
                print(f"  ❌ 读取目录失败: {e}")
                results.append(("FloSCRIPT 示例", False))

            break

    if not found:
        print("  ❌ 未找到 FloSCRIPT 示例目录")
        results.append(("FloSCRIPT 示例", False))

    return results


def test_pip_packages():
    """尝试通过 pip 安装 API"""
    print_header("6. pip 安装测试")

    results = []

    packages = [
        "flotherm_api",
        "ftapi",
        "flotherm",
    ]

    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 解析版本
                lines = result.stdout.split('\n')
                version = "未知"
                for line in lines:
                    if line.startswith('Version:'):
                        version = line.split(':', 1)[1].strip()
                        break
                print_result(f"pip: {package}", True, f"版本 {version}")
                results.append((package, True))
            else:
                print_result(f"pip: {package}", False, "未安装")
                results.append((package, False))
        except Exception as e:
            print_result(f"pip: {package}", False, str(e))
            results.append((package, False))

    # 提供安装建议
    print("\n  💡 安装建议:")
    print("    pip install pywin32        # COM API 支持")
    print("    pip install flotherm_api   # 原生 API (如果可用)")

    return results


def generate_report(all_results):
    """生成测试报告"""
    print_header("测试报告总结")

    total = 0
    passed = 0

    for category, results in all_results:
        if results:
            cat_passed = sum(1 for _, success, *_ in results if success)
            cat_total = len(results)
            total += cat_total
            passed += cat_passed

            status = "✅" if cat_passed == cat_total else "⚠️" if cat_passed > 0 else "❌"
            print(f"  {status} {category}: {cat_passed}/{cat_total} 通过")

    print(f"\n  总计: {passed}/{total} 测试通过")

    # 给出建议
    print("\n" + "-" * 60)
    print("  📋 建议方案:")

    if passed == 0:
        print("""
  1. 确认 FloTHERM 已正确安装
  2. 检查安装时是否勾选了 Python API 组件
  3. 尝试安装 pywin32: pip install pywin32
  4. 联系 Siemens 支持获取你版本的 API
  5. 使用 FloSCRIPT 宏作为替代方案（需要 GUI）
""")
    else:
        # 检查哪些可用
        com_available = any(r[1] for r in all_results[1][1]) if len(all_results) > 1 else False
        python_available = any(r[1] for r in all_results[0][1]) if len(all_results) > 0 else False

        if python_available:
            print("""
  ✅ Python 原生 API 可用！
  你可以使用 import flotherm 或 from ftapi import FloTHERM 进行自动化开发。
""")
        elif com_available:
            print("""
  ✅ COM API 可用！
  你可以使用 win32com.client.Dispatch("Flotherm.Application") 进行自动化开发。
""")
        else:
            print("""
  ⚠️ 没有找到可用的编程接口
  建议使用 FloSCRIPT 宏方式进行半自动化操作。
""")


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          FloTHERM API 可用性测试脚本 v1.0                  ║
║                                                            ║
║  用于检测 FloTHERM 的各种自动化接口是否可用              ║
╚════════════════════════════════════════════════════════════╝
""")

    print(f"系统平台: {sys.platform}")
    print(f"Python 版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")

    all_results = []

    # 运行所有测试
    all_results.append(("Python 原生 API", test_python_native_api()))
    all_results.append(("COM API", test_com_api()))
    all_results.append(("安装目录", test_flotherm_installation()))
    all_results.append(("命令行接口", test_command_line()))
    all_results.append(("FloSCRIPT 示例", test_floscript_examples()))
    all_results.append(("pip 包", test_pip_packages()))

    # 生成报告
    generate_report(all_results)

    print("\n" + "=" * 60)
    print("  测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
