#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 统一CLI入口
"""
import os
import sys
import glob
import re
from pathlib import Path

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

try:
    from video2adofai import generate_video_adofai, DEFAULT_FPS, DEFAULT_ZOOM, natural_sort_key
    from video2adofai_v2 import generate_video_adofai_v2
    from image2adofai import generate_adofai
    V2_OK = True
except ImportError as e:
    try:
        from video2adofai import generate_video_adofai, DEFAULT_FPS, DEFAULT_ZOOM, natural_sort_key
        from image2adofai import generate_adofai
        V2_OK = False
    except ImportError:
        print(f"错误: 缺少必需模块 - {e}")
        sys.exit(1)

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
def extract_frames():
    """视频 → 帧"""
    if not CV2_OK:
        print("需要安装 opencv-python: pip install opencv-python")
        return
    
    print("\n[视频提取帧]")
    video = get_input("视频路径")
    if not os.path.exists(video):
        print("  文件不存在")
        return
    
    group = get_input("每组帧数", 1000, int, lambda x: (x>0, "必须>0"))
    fmt = get_input("图片格式 (png/jpg)", "png")
    
    # 提取
    import cv2
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        print("  无法打开视频")
        return
    
    name = Path(video).stem
    out_dir = Path(video).parent / name
    out_dir.mkdir(exist_ok=True)
    
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"  总帧数: {total}, FPS: {fps:.1f}")
    
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        count += 1
        g = (count-1) // group + 1
        part_dir = out_dir / f"part{g}"
        part_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(part_dir / f"{count}.{fmt}"), frame)
        if count % 100 == 0:
            print(f"  {count}/{total}")
    
    cap.release()
    print(f"完成: {count} 帧 → {out_dir}")

# ========== 2. 批量缩放 ==========
def batch_resize():
    """批量缩放图片"""
    if not PIL_OK:
        print("需要安装 Pillow: pip install Pillow")
        return
    
    print("\n[批量缩放]")
    src = get_input("输入目录(含part*/)")
    if not os.path.isdir(src):
        print("  目录不存在")
        return
    
    w = get_input("目标宽度", 120, int, lambda x: (x>0, "必须>0"))
    h = get_input("目标高度", 90, int, lambda x: (x>0, "必须>0"))
    
    src_p = Path(src)
    dst_p = src_p.parent / f"{src_p.name}_resized"
    
    # 找part
    parts = []
    for item in src_p.iterdir():
        if item.is_dir() and re.match(r'^part\d+', item.name, re.I):
            imgs = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                imgs.extend(item.glob(ext))
            if imgs:
                parts.append((item.name, sorted(imgs, key=lambda x: natural_sort_key(x.name))))
    
    if not parts:
        print("  未找到part*文件夹")
        return
    
    parts.sort(key=lambda x: natural_sort_key(x[0]))
    print(f"  找到{len(parts)}个分组")
    
    total = 0
    for pname, imgs in parts:
        out = dst_p / pname
        out.mkdir(parents=True, exist_ok=True)
        for img_p in imgs:
            try:
                img = Image.open(img_p)
                resized = img.resize((w, h), Image.Resampling.LANCZOS)
                resized.save(out / img_p.name)
                total += 1
            except:
                pass
        print(f"  {pname}: {len(imgs)}")
    
    print(f"完成: {total} 张 → {dst_p}")

# ========== 3. 单张图片转ADOFAI ==========
def image_to_adofai():
    """图片 → ADOFAI"""
    print("\n[单张图片转ADOFAI]")
    img = get_input("图片路径")
    if not os.path.exists(img):
        print("  不存在")
        return
    
    out = Path(__file__).parent / f"{Path(img).stem}.adofai"
    y = get_input("Y偏移(行间距)", 0.9, float, lambda x: (x>0, "必须>0"))
    
    if generate_adofai(img, str(out), y):
        print(f"完成: {out}")
    else:
        print("  失败")

# ========== 4. 帧文件夹 → ADOFAI ==========
def get_frames():
    """获取帧文件"""
    folder = get_input("帧文件夹路径")
    if not os.path.isdir(folder):
        print("  不存在")
        return None
    
    files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        files.extend(glob.glob(os.path.join(folder, ext)))
    
    if not files:
        print("  未找到图片")
        return None
    
    files = sorted(files, key=natural_sort_key)
    print(f"  找到{len(files)}个文件")
    return files

def frames_to_adofai(use_v2=False):
    """单文件夹帧 → ADOFAI"""
    ver = "v2" if use_v2 else "v1"
    print(f"\n[单文件夹转ADOFAI ({ver})]")
    
    frames = get_frames()
    if not frames:
        return
    
    out = Path(__file__).parent / f"output_{ver}.adofai"
    fps = get_input("FPS", DEFAULT_FPS, float, lambda x: (x>0, "必须>0"))
    zoom = get_input("Zoom", DEFAULT_ZOOM, int, lambda x: (x>0, "必须>0"))
    
    print(f"  帧数: {len(frames)}, FPS: {fps}, Zoom: {zoom}%")
    
    try:
        if use_v2:
            generate_video_adofai_v2(frames, str(out), fps, zoom)
        else:
            generate_video_adofai(frames, str(out), fps, zoom)
        print(f"完成: {out}")
    except Exception as e:
        print(f"  失败: {e}")

# ========== 5. 分组帧 → ADOFAI ==========
def get_parts(folder):
    """获取part分组"""
    p = Path(folder)
    if not p.is_dir():
        return None
    
    parts = []
    for item in p.iterdir():
        if item.is_dir() and re.match(r'^part\d+$', item.name, re.I):
            files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                files.extend(glob.glob(str(item / ext)))
            if files:
                parts.append((item.name, sorted(files, key=natural_sort_key)))
    
    if not parts:
        return None
    
    parts.sort(key=lambda x: natural_sort_key(x[0]))
    return parts

def grouped_to_adofai(use_v2=False):
    """分组帧 → 多个ADOFAI"""
    ver = "v2" if use_v2 else "v1"
    print(f"\n[分组转ADOFAI ({ver})]")
    
    folder = get_input("输入目录(含part*/)")
    parts = get_parts(folder)
    if not parts:
        print("  未找到part*")
        return
    
    print(f"  找到{len(parts)}个分组")
    
    out_dir = Path(__file__).parent / f"{Path(folder).name}_levels_{ver}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fps = get_input("FPS", DEFAULT_FPS, float, lambda x: (x>0, "必须>0"))
    zoom = get_input("Zoom", DEFAULT_ZOOM, int, lambda x: (x>0, "必须>0"))
    
    ok = 0
    for pname, frames in parts:
        out = out_dir / f"{pname}.adofai"
        try:
            if use_v2:
                generate_video_adofai_v2(frames, str(out), fps, zoom)
            else:
                generate_video_adofai(frames, str(out), fps, zoom)
            print(f"  {pname}: OK")
            ok += 1
        except Exception as e:
            print(f"  {pname}: 失败 - {e}")
    
    print(f"完成: {ok}/{len(parts)} → {out_dir}")

# ========== 主菜单 ==========
def main():
    print("=" * 50)
    print("  ADOFAI 工具集")
    print("=" * 50)
    
    while True:
        print("\n请选择:")
        print("  [1] 视频提取帧")
        print("  [2] 批量缩放图片")
        print("  [3] 单张图片 → ADOFAI")
        print("  [4] 单文件夹帧 → ADOFAI (v1)")
        if V2_OK:
            print("  [5] 单文件夹帧 → ADOFAI (v2高效)")
        print("  [6] 分组帧 → ADOFAI (v1)")
        if V2_OK:
            print("  [7] 分组帧 → ADOFAI (v2高效)")
        print("  [0] 退出")
        
        choice = get_input("\n选择", "1")
        
        if choice == "1":
            extract_frames()
        elif choice == "2":
            batch_resize()
        elif choice == "3":
            image_to_adofai()
        elif choice == "4":
            frames_to_adofai(False)
        elif choice == "5" and V2_OK:
            frames_to_adofai(True)
        elif choice == "6":
            grouped_to_adofai(False)
        elif choice == "7" and V2_OK:
            grouped_to_adofai(True)
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
