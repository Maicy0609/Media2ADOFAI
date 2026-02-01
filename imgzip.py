#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量缩放图片工具（Pillow 版，无需 FFmpeg）
支持分组文件夹（part1/part2...）或单文件夹模式
"""
import os
import sys
import re
from pathlib import Path
from PIL import Image

def natural_sort_key(s):
    """自然排序：1.png, 2.png, ..., 10.png"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

def resize_image(input_path, output_path, mode, width=0, height=0, percent=0, quality=95):
    """
    缩放单张图片
    
    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径  
        mode: 模式 ('width', 'height', 'fixed', 'percent')
        width: 目标宽度（mode=width/fixed时）
        height: 目标高度（mode=height/fixed时）
        percent: 缩放百分比（mode=percent时）
        quality: JPEG质量（默认95）
    
    返回:
        tuple: (success: bool, new_size: tuple or None, error: str or None)
    """
    try:
        img = Image.open(input_path)
        orig_w, orig_h = img.size
        
        if mode == 'width':
            new_w = width
            new_h = int(orig_h * (width / orig_w))
        elif mode == 'height':
            new_h = height
            new_w = int(orig_w * (height / orig_h))
        elif mode == 'fixed':
            new_w, new_h = width, height
        elif mode == 'percent':
            new_w = int(orig_w * percent / 100)
            new_h = int(orig_h * percent / 100)
        else:
            return False, None, f"未知模式: {mode}"
        
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        file_ext = str(input_path).lower().split('.')[-1]
        if file_ext in ['jpg', 'jpeg']:
            resized.save(output_path, 'JPEG', quality=quality, optimize=True)
        elif file_ext == 'png':
            resized.save(output_path, 'PNG', optimize=True, compress_level=9)
        else:
            resized.save(output_path)
            
        return True, (new_w, new_h), None
        
    except Exception as e:
        return False, None, str(e)

def batch_resize(input_folder, output_folder, mode, width=0, height=0, percent=0, 
                group_mode=True, extensions=None, verbose=True):
    """
    批量缩放文件夹中的图片
    
    参数:
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        mode: 缩放模式 ('width', 'height', 'fixed', 'percent')
        width: 目标宽度
        height: 目标高度  
        percent: 缩放百分比
        group_mode: 是否为分组模式（处理part1/part2子文件夹）
        extensions: 处理的扩展名列表（默认 ['.png', '.jpg', '.jpeg']）
        verbose: 是否打印进度
    
    返回:
        dict: {'success': 成功数, 'fail': 失败数, 'errors': 错误列表}
    """
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg']
    
    input_path = Path(input_folder).expanduser().resolve()
    output_path = Path(output_folder).expanduser().resolve()
    
    if not input_path.exists():
        raise FileNotFoundError(f"输入路径不存在: {input_path}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 收集文件
    if group_mode:
        part_dirs = []
        for item in input_path.iterdir():
            if item.is_dir() and re.match(r'^part\d+', item.name, re.IGNORECASE):
                files = []
                for ext in extensions:
                    files.extend(item.glob(f"*{ext}"))
                    files.extend(item.glob(f"*{ext.upper()}"))
                if files:
                    files = sorted(files, key=natural_sort_key)
                    part_dirs.append((item, files))
        
        if not part_dirs:
            raise ValueError(f"未找到有效的 part* 子文件夹: {input_path}")
        
        part_dirs.sort(key=lambda x: natural_sort_key(x[0].name))
        sources = part_dirs
    else:
        files = []
        for ext in extensions:
            files.extend(input_path.glob(f"*{ext}"))
            files.extend(input_path.glob(f"*{ext.upper()}"))
        if not files:
            raise ValueError(f"未找到图片文件: {input_path}")
        files = sorted(files, key=natural_sort_key)
        sources = [(input_path, files)]
    
    # 处理
    total_success = 0
    total_fail = 0
    errors = []
    
    desc = ""
    if mode == 'width':
        desc = f"宽{width}px"
    elif mode == 'height':
        desc = f"高{height}px"
    elif mode == 'fixed':
        desc = f"{width}x{height}"
    elif mode == 'percent':
        desc = f"{percent}%"
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"🚀 开始批量处理 [{desc}]")
        print(f"📂 输入: {input_path}")
        print(f"📁 输出: {output_path}")
        print(f"{'='*50}")
    
    for source_dir, img_files in sources:
        if group_mode:
            rel_name = source_dir.name
            current_output = output_path / rel_name
        else:
            current_output = output_path
        
        current_output.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            print(f"\n📦 {source_dir.name if group_mode else '处理中'} ({len(img_files)} 张)")
        
        for i, file_path in enumerate(img_files, 1):
            output_file = current_output / file_path.name
            
            success, new_size, error = resize_image(
                file_path, output_file, mode, width, height, percent
            )
            
            if success:
                total_success += 1
                if verbose and (i % 10 == 0 or i == len(img_files)):
                    print(f"  ✅ [{i}/{len(img_files)}] {file_path.name} → {new_size[0]}x{new_size[1]}")
            else:
                total_fail += 1
                errors.append(f"{file_path}: {error}")
                if verbose:
                    print(f"  ❌ [{i}/{len(img_files)}] {file_path.name}: {error}")
    
    if verbose:
        print(f"\n{'='*50}")
        print("📊 处理完成!")
        print(f"   ✅ 成功: {total_success}")
        print(f"   ❌ 失败: {total_fail}")
        print(f"{'='*50}")
    
    return {
        'success': total_success,
        'fail': total_fail,
        'errors': errors,
        'output_path': str(output_path)
    }

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量缩放图片工具')
    parser.add_argument('input', help='输入文件夹路径')
    parser.add_argument('output', help='输出文件夹路径')
    
    # 缩放模式
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-W', '--width', type=int, help='指定宽度，高度等比例')
    group.add_argument('-H', '--height', type=int, help='指定高度，宽度等比例')
    group.add_argument('-F', '--fixed', nargs=2, type=int, metavar=('W', 'H'),
                      help='强制指定宽高（可能变形）')
    group.add_argument('-P', '--percent', type=float, help='缩放百分比（如 50）')
    
    parser.add_argument('--no-group', action='store_true',
                       help='非分组模式（不查找part1/part2子文件夹）')
    parser.add_argument('-q', '--quality', type=int, default=95,
                       help='JPEG质量（默认95）')
    
    args = parser.parse_args()
    
    # 确定模式
    if args.width:
        mode, w, h, p = 'width', args.width, 0, 0
    elif args.height:
        mode, w, h, p = 'height', 0, args.height, 0
    elif args.fixed:
        mode, w, h, p = 'fixed', args.fixed[0], args.fixed[1], 0
    elif args.percent:
        mode, w, h, p = 'percent', 0, 0, args.percent
    
    try:
        result = batch_resize(
            input_folder=args.input,
            output_folder=args.output,
            mode=mode,
            width=w,
            height=h,
            percent=p,
            group_mode=not args.no_group,
            verbose=True
        )
        
        if result['fail'] > 0:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
