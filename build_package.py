#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CADChat v0.11 打包脚本
将项目打包为可分发的格式
"""

import os
import sys
import shutil
import subprocess

DIST_DIR = "dist"
PACKAGE_NAME = "CADChat_v0.11"

EXCLUDE_DIRS = [
    '__pycache__',
    '.git',
    '.vscode',
    'browser_data',
    '.pytest_cache',
    'node_modules',
    'venv',
    'env',
    '.venv',
    '.env',
]

EXCLUDE_EXTENSIONS = [
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.db',
    '.log',
]

EXCLUDE_FILES = [
    'local_cache.db',
    '.DS_Store',
    'Thumbs.db',
    'command_embeddings_bge_m3.npy',
    'command_embeddings.npy',
    '.tmp.npy',
]

def should_exclude(path):
    """检查是否应该排除该文件/目录"""
    basename = os.path.basename(path)

    for exclude in EXCLUDE_DIRS:
        if exclude in path.split(os.sep):
            return True

    for ext in EXCLUDE_EXTENSIONS:
        if path.endswith(ext):
            return True

    for fname in EXCLUDE_FILES:
        if basename == fname or fname in basename:
            return True

    return False

def copy_tree(src, dst):
    """复制目录树，排除不需要的文件"""
    if should_exclude(src):
        return

    if os.path.isfile(src):
        if should_exclude(src):
            return
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  复制: {src}")
        return

    os.makedirs(dst, exist_ok=True)

    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)

        if should_exclude(src_item):
            print(f"  跳过: {src_item}")
            continue

        if os.path.isdir(src_item):
            copy_tree(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)
            print(f"  复制: {src_item}")

def create_package():
    """创建分发包"""
    print("=" * 60)
    print("CADChat v0.11 打包工具")
    print("=" * 60)

    package_dir = os.path.join(DIST_DIR, PACKAGE_NAME)

    if os.path.exists(package_dir):
        print(f"\n清理旧包: {package_dir}")
        shutil.rmtree(package_dir)

    print(f"\n创建包目录: {package_dir}")
    os.makedirs(package_dir, exist_ok=True)

    # 复制项目文件
    print("\n复制项目文件...")

    # 根目录文件
    root_files = [
        'README.md',
        'CLIENT_GUIDE.md',
        'start_client.bat',
    ]

    for f in root_files:
        src = f
        if os.path.exists(src):
            shutil.copy2(src, package_dir)
            print(f"  复制: {src}")

    # server 目录
    print("\n复制 server 目录...")
    server_src = "server"
    server_dst = os.path.join(package_dir, "server")
    copy_tree(server_src, server_dst)

    # 根目录 Python 文件
    print("\n复制 Python 文件...")
    for f in ['main_gui_cloud.py', 'cloud_client.py', 'kimi_browser.py', 'cad_connector.py']:
        if os.path.exists(f):
            shutil.copy2(f, package_dir)
            print(f"  复制: {f}")

    print("\n" + "=" * 60)
    print("打包完成!")
    print("=" * 60)
    print(f"\n包位置: {os.path.abspath(package_dir)}")
    print("\n包含文件:")
    for root, dirs, files in os.walk(package_dir):
        level = root.replace(package_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... 还有 {len(files)-5} 个文件")

def build_exe():
    """使用 PyInstaller 构建可执行文件"""
    print("\n检查 PyInstaller...")

    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller 未安装，跳过构建 EXE")
        print("如需构建 EXE，请运行: pip install pyinstaller")
        return

    print("\n开始构建 EXE...")

    # PyInstaller 配置文件
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_gui_cloud.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('server/*.txt', 'server'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CADChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CADChat',
)
'''

    with open('CADChat.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    subprocess.run(['pyinstaller', 'CADChat.spec', '--clean'], check=True)

    print("\n构建完成!")
    print(f"EXE 位置: {os.path.join('dist', 'CADChat', 'CADChat.exe')}")

if __name__ == "__main__":
    create_package()

    if len(sys.argv) > 1 and sys.argv[1] == '--exe':
        build_exe()
