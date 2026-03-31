#!/usr/bin/env python
"""
PyInstaller打包脚本
将main.py打包成独立可执行程序
"""

import contextlib
import PyInstaller.__main__
import os
import sys
from src.info import __version__, __app_name__

project_folder_name = "Resource Integrity Tool"

# PyInstaller参数
args = [
    'src/main.py',
    f'--name={__app_name__}',  # 可执行程序名称
    '--onefile',  # 生成单个exe文件（不使用的话会生成文件夹）
    '--windowed',  # GUI应用，不显示控制台窗口
    '--icon=johnson.ico',
    '--hidden-import=PySide6',
    '--hidden-import=blake3',
    '--hidden-import=xxhash',
]

out_dir = os.path.join('dist', f'{project_folder_name} {__version__}')
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# 把config文件夹复制到输出目录
import shutil
config_dst = os.path.join(out_dir, 'config')
if os.path.exists(config_dst):
    shutil.rmtree(config_dst)
shutil.copytree('config', config_dst)

# 删除测试缓存
config_dst_user = os.path.join(config_dst, 'UserConfig.json')
with contextlib.suppress(FileNotFoundError):
    os.remove(config_dst_user)

# 开始打包
print("开始打包...")
print(f"输出目录: {out_dir}")
print()

PyInstaller.__main__.run(args)

# 确认操作系统平台后缀
if sys.platform == "win32":
    suffix = ".exe"
elif sys.platform == "darwin":
    suffix = ".app"
else:
    suffix = ""

# 把输出的文件拷贝到输出目录
exe_src = os.path.join('dist', f'{__app_name__}{suffix}')
exe_dst = os.path.join(out_dir, f'{__app_name__}{__version__}{suffix}')
shutil.move(exe_src, exe_dst)

print("\n✅打包完成！")
print(f"可执行文件位置: {os.path.join(out_dir, f'{__app_name__}{__version__}{suffix}')}")
