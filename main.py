#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 交互式入口
"""

import os
import sys
import glob
import re
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 检查依赖
try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

from core import (
    extract_frames,
    batch_resize,
    generate_image_adofai,
    generate_video_adofai,
    generate_video_adofai_v2
)
from utils import natural_sort_key, find_part_folders, find_image_files, print_progress
from config import DEFAULT_FPS, DEFAULT_ZOOM, DEFAULT_Y_OFFSET


def get_input(prompt, default=None, type_=str, check=None):
    """统一输入函数"""
    while True:
        txt = input(f"{prompt} (默认: {default}): " if default else f"{prompt}: ").strip()
        if not txt:
            if default is None:
                print("  不能为空")
                continue
            return default
        try:
            val = type_(txt)
        except ValueError:
            print(f"  需要{type_.__name__}类型")
            continue
        if check:
            ok, msg = check(val)
            if not ok:
                print(f"  {msg}")
                continue
        return val


# ========== 1. 视频提取帧 ==========
def menu_extract_frames():
    """视频 → 帧"""
    if not CV2_OK:
        print("需要安装 opencv-python: pip install opencv-python")
        return
    
    print("\n[视频提取帧]")
    video = get_input("视频路径")
    if not os.path.exists(video):
        print("  文件不存在")
        return
    
    group = get_input("每组帧数", 1000, int, lambda x: (x > 0, "必须>0"))
    fmt = get_input("图片格式 (png/jpg)", "png")
    
    result = extract_frames(
        video_path=video,
        image_format=fmt,
        group_size=group,
        verbose=True
    )
    
    if not result['success']:
        print(f"  失败: {result['error']}")


# ========== 2. 批量缩放 ==========
def menu_batch_resize():
    """批量缩放图片"""
    if not PIL_OK:
        print("需要安装 Pillow: pip install Pillow")
        return
    
    print("\n[批量缩放]")
    src = get_input("输入目录(含part*/)")
    if not os.path.isdir(src):
        print("  目录不存在")
        return
    
    w = get_input("目标宽度", 120, int, lambda x: (x > 0, "必须>0"))
    h = get_input("目标高度", 90, int, lambda x: (x > 0, "必须>0"))
    
    src_p = Path(src)
    dst_p = src_p.parent / f"{src_p.name}_resized"
    
    try:
        result = batch_resize(
            input_folder=src,
            output_folder=str(dst_p),
            mode='fixed',
            width=w,
            height=h,
            group_mode=True,
            verbose=True
        )
    except Exception as e:
        print(f"  错误: {e}")


# ========== 3. 单张图片转ADOFAI ==========
def menu_image_to_adofai():
    """图片 → ADOFAI"""
    print("\n[单张图片转ADOFAI]")
    img = get_input("图片路径")
    if not os.path.exists(img):
        print("  不存在")
        return
    
    out = Path(__file__).parent / f"{Path(img).stem}.adofai"
    y = get_input("Y偏移(行间距)", DEFAULT_Y_OFFSET, float, lambda x: (x > 0, "必须>0"))
    
    try:
        generate_image_adofai(img, str(out), y)
    except Exception as e:
        print(f"  失败: {e}")


# ========== 4. 帧文件夹 → ADOFAI ==========
def get_frames():
    """获取帧文件"""
    folder = get_input("帧文件夹路径")
    if not os.path.isdir(folder):
        print("  不存在")
        return None
    
    files = find_image_files(folder)
    if not files:
        print("  未找到图片")
        return None
    
    print(f"  找到{len(files)}个文件")
    return files


def menu_frames_to_adofai(use_v2=False):
    """单文件夹帧 → ADOFAI"""
    ver = "v2" if use_v2 else "v1"
    print(f"\n[单文件夹转ADOFAI ({ver})]")
    
    frames = get_frames()
    if not frames:
        return
    
    out = Path(__file__).parent / f"output_{ver}.adofai"
    fps = get_input("FPS", DEFAULT_FPS, float, lambda x: (x > 0, "必须>0"))
    zoom = get_input("Zoom", DEFAULT_ZOOM, int, lambda x: (x > 0, "必须>0"))
    
    print(f"  帧数: {len(frames)}, FPS: {fps}, Zoom: {zoom}%")
    
    try:
        if use_v2:
            generate_video_adofai_v2(frames, str(out), fps, zoom)
        else:
            generate_video_adofai(frames, str(out), fps, zoom)
    except Exception as e:
        print(f"  失败: {e}")


# ========== 5. 分组帧 → ADOFAI ==========
def menu_grouped_to_adofai(use_v2=False):
    """分组帧 → 多个ADOFAI"""
    ver = "v2" if use_v2 else "v1"
    print(f"\n[分组转ADOFAI ({ver})]")
    
    folder = get_input("输入目录(含part*/)")
    parts = find_part_folders(folder)
    if not parts:
        print("  未找到part*")
        return
    
    total_parts = len(parts)
    print(f"  找到{total_parts}个分组")
    
    out_dir = Path(__file__).parent / f"{Path(folder).name}_levels_{ver}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fps = get_input("FPS", DEFAULT_FPS, float, lambda x: (x > 0, "必须>0"))
    zoom = get_input("Zoom", DEFAULT_ZOOM, int, lambda x: (x > 0, "必须>0"))
    
    print(f"\n开始处理 {total_parts} 个分组...\n")
    
    ok = 0
    for idx, (pname, frames) in enumerate(parts, 1):
        out = out_dir / f"{pname}.adofai"
        frame_count = len(frames)
        
        # 显示当前part进度
        print(f"[{idx}/{total_parts}] {pname} ({frame_count} 帧)")
        
        try:
            if use_v2:
                generate_video_adofai_v2([str(f) for f in frames], str(out), fps, zoom, verbose=True)
            else:
                generate_video_adofai([str(f) for f in frames], str(out), fps, zoom, verbose=True)
            ok += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        # 显示总体进度
        print_progress(idx, total_parts, prefix="  总进度", suffix="")
        print()  # 换行
    
    print(f"\n{'='*50}")
    print(f"完成: {ok}/{total_parts} 个分组成功")
    print(f"输出目录: {out_dir}")
    print(f"{'='*50}")


# ========== 主菜单 ==========
def main():
    print("=" * 50)
    print("  ADOFAI 工具集")
    print("  将图片或视频转换成ADOFAI关卡文件")
    print("=" * 50)
    
    while True:
        print("\n请选择:")
        print("  [1] 视频提取帧")
        print("  [2] 批量缩放图片")
        print("  [3] 单张图片 → ADOFAI")
        print("  [4] 单文件夹帧 → ADOFAI (v1)")
        print("  [5] 单文件夹帧 → ADOFAI (v2高效)")
        print("  [6] 分组帧 → ADOFAI (v1)")
        print("  [7] 分组帧 → ADOFAI (v2高效)")
        print("  [0] 退出")
        
        choice = get_input("\n选择", "1")
        
        if choice == "1":
            menu_extract_frames()
        elif choice == "2":
            menu_batch_resize()
        elif choice == "3":
            menu_image_to_adofai()
        elif choice == "4":
            menu_frames_to_adofai(False)
        elif choice == "5":
            menu_frames_to_adofai(True)
        elif choice == "6":
            menu_grouped_to_adofai(False)
        elif choice == "7":
            menu_grouped_to_adofai(True)
        elif choice == "0":
            print("\n再见")
            sys.exit(0)
        else:
            print("  无效选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
