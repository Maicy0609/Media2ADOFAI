#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 公共工具函数
"""

import re
import os
import sys
from pathlib import Path


def natural_sort_key(s):
    """
    自然排序key函数，将数字部分转为整数比较
    用于正确排序: 1.png, 2.png, ..., 10.png, 11.png
    
    参数:
        s: 字符串或Path对象
    
    返回:
        list: 排序用的key列表
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


def format_value(val):
    """
    ADOFAI 格式化值（小写 true/false，类JSON格式）
    
    参数:
        val: 要格式化的值（bool/int/float/str/list）
    
    返回:
        str: 格式化后的字符串
    """
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return str(val)
    elif isinstance(val, str):
        return f'"{val}"'
    elif isinstance(val, list):
        items = [format_value(v) for v in val]
        return f'[{", ".join(items)}]'
    return str(val)


def clean_path(path):
    """
    清理路径字符串（去除引号、&符号等）
    
    参数:
        path: 原始路径字符串
    
    返回:
        str: 清理后的路径
    """
    if not path:
        return path
    path = path.strip()
    while (len(path) >= 2 and 
           ((path.startswith('"') and path.endswith('"')) or 
            (path.startswith("'") and path.endswith("'")))):
        path = path[1:-1].strip()
    if path.startswith('&'):
        path = path[1:].strip()
    return path


def get_script_dir():
    """获取脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))


def resolve_output_path(user_output, input_path, script_dir):
    """
    解析输出路径
    
    参数:
        user_output: 用户指定的输出路径（可为空）
        input_path: 输入文件路径
        script_dir: 脚本目录
    
    返回:
        str: 完整的输出路径
    """
    if not user_output:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(script_dir, f"{base_name}.adofai")
    user_output = clean_path(user_output)
    if os.path.isabs(user_output):
        return user_output
    return os.path.join(script_dir, user_output)


def pixel_to_hex(r, g, b, a=255):
    """
    将RGBA像素值转换为十六进制颜色字符串
    
    参数:
        r, g, b, a: RGBA值（0-255）
    
    返回:
        str: 十六进制颜色字符串（如 "ff0000ff"）
    """
    return f"{r:02x}{g:02x}{b:02x}{a:02x}"


def find_part_folders(folder_path):
    """
    查找文件夹中的part分组（part1, part2, ...）
    
    参数:
        folder_path: 文件夹路径
    
    返回:
        list: [(文件夹名, 文件列表), ...] 按自然排序
    """
    p = Path(folder_path)
    if not p.is_dir():
        return None
    
    parts = []
    for item in p.iterdir():
        if item.is_dir() and re.match(r'^part\d+$', item.name, re.IGNORECASE):
            files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                files.extend(item.glob(ext))
                files.extend(item.glob(ext.upper()))
            if files:
                parts.append((item.name, sorted(files, key=natural_sort_key)))
    
    if not parts:
        return None
    
    parts.sort(key=lambda x: natural_sort_key(x[0]))
    return parts


def find_image_files(folder_path, extensions=None):
    """
    查找文件夹中的图片文件
    
    参数:
        folder_path: 文件夹路径
        extensions: 扩展名列表（默认 ['.png', '.jpg', '.jpeg']）
    
    返回:
        list: 图片文件路径列表（按自然排序）
    """
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg']
    
    p = Path(folder_path)
    if not p.is_dir():
        return None
    
    files = []
    for ext in extensions:
        files.extend(p.glob(f"*{ext}"))
        files.extend(p.glob(f"*{ext.upper()}"))
    
    if not files:
        return None
    
    return sorted(files, key=natural_sort_key)


def format_file_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def print_progress(current, total, prefix="", suffix="", bar_width=40, refresh_percent=5):
    """
    打印进度条（每refresh_percent%刷新一次）
    
    参数:
        current: 当前进度
        total: 总数
        prefix: 前缀文字
        suffix: 后缀文字
        bar_width: 进度条宽度
        refresh_percent: 刷新百分比（默认5%）
    """
    if total == 0:
        return
    
    percent = current / total * 100
    
    # 检查是否需要刷新（每refresh_percent%刷新一次，或者完成时）
    checkpoint = int(percent / refresh_percent)
    prev_checkpoint = int((current - 1) / total * 100 / refresh_percent) if current > 1 else -1
    
    # 只在达到新的检查点或完成时刷新
    if checkpoint > prev_checkpoint or current == total:
        filled = int(bar_width * current / total)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # 使用\r回到行首，覆盖之前的输出
        line = f"\r{prefix} |{bar}| {percent:5.1f}% ({current}/{total}) {suffix}"
        sys.stdout.write(line)
        
        if current == total:
            sys.stdout.write("\n")
        
        sys.stdout.flush()


def print_progress_inline(current, total, prefix=""):
    """
    打印单行进度（简洁版，每5%刷新）
    
    参数:
        current: 当前进度
        total: 总数
        prefix: 前缀文字
    """
    if total == 0:
        return
    
    percent = current / total * 100
    checkpoint = int(percent / 5)
    prev_checkpoint = int((current - 1) / total * 100 / 5) if current > 1 else -1
    
    if checkpoint > prev_checkpoint or current == total:
        print(f"\r  {prefix} {percent:5.1f}% ({current}/{total})", end="")
        if current == total:
            print()  # 完成时换行
        sys.stdout.flush()
