#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 交互式 CLI（完整整合版）
支持：
  - 视频提取帧（Video → Frames）
  - 批量缩放图片（Batch Resize）
  - 视频帧转 ADOFAI（单文件夹 / 分组）
  - 单张图片转 ADOFAI
"""
import os
import sys
import glob
import re
import shutil
from pathlib import Path

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from video2adofai import generate_video_adofai, DEFAULT_FPS, DEFAULT_ZOOM, natural_sort_key
except ImportError as e:
    print(f"无法导入 video2adofai 模块: {e}")
    sys.exit(1)

try:
    from image2adofai import generate_adofai
except ImportError as e:
    print(f"无法导入 image2adofai 模块: {e}")
    sys.exit(1)

def print_header():
    print("=" * 60)
    print("  ADOFAI 工具集  ")
    print("=" * 60)
    print()

def print_menu():
    print("\n请选择功能:")
    print("  [1] 🎬 视频提取帧 (Video → Frames)")
    print("  [2] 🖼️  批量缩放图片 (Batch Resize)")
    print("  [3] 🎮 视频帧转 ADOFAI（单文件夹）")
    print("  [4] 🎮 分组帧（part1/part2...）转多个 ADOFAI")
    print("  [5] 🖼️  单张图片转 ADOFAI")
    print("  [0] 退出")
    print()

def get_input(prompt, default=None, input_type=str, validator=None):
    while True:
        if default is not None:
            user_input = input(f"{prompt} (默认: {default}): ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()
        if not user_input and default is None:
            print("  输入不能为空，请重新输入")
            continue
        if not user_input:
            return default
        try:
            if input_type == int:
                value = int(user_input)
            elif input_type == float:
                value = float(user_input)
            else:
                value = user_input
        except ValueError:
            print(f"  输入格式错误，请输入{input_type.__name__}类型")
            continue
        if validator:
            is_valid, error_msg = validator(value)
            if not is_valid:
                print(f"  ⚠️ {error_msg}")
                continue
        return value

# ========== 1. 视频提取帧功能 ==========
def extract_video_frames():
    print("\n" + "=" * 60)
    print("  🎬 视频提取帧 (Video → Frames)")
    print("=" * 60)

    if not CV2_AVAILABLE:
        print("❌ 错误：未安装 OpenCV (cv2)")
        print("请运行: pip install opencv-python")
        return

    video_path = get_input("请输入视频文件路径")
    video_path = video_path.strip('"').strip("'")

    if not os.path.exists(video_path):
        print(f"❌ 错误：视频文件不存在 - {video_path}")
        return

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    script_dir = Path(__file__).parent.resolve()

    default_output = script_dir / video_name
    output_base = get_input("输出目录（直接回车使用默认）", default=str(default_output))
    output_base = output_base.strip('"').strip("'")

    img_format = get_input("图片格式 (png/jpg)", default="png")
    if img_format not in ['png', 'jpg', 'jpeg', 'bmp']:
        print("⚠️  不支持的格式，使用默认 png")
        img_format = 'png'

    group_size = get_input(
        "每组多少帧（分组存储）",
        default=1000,
        input_type=int,
        validator=lambda x: (x > 0, "每组帧数必须大于0")
    )

    print(f"\n{'-'*50}")
    print("📋 处理摘要:")
    print(f"   视频: {video_path}")
    print(f"   输出: {output_base}")
    print(f"   格式: {img_format}")
    print(f"   分组: 每 {group_size} 帧一组")
    print(f"{'-'*50}")

    confirm = get_input("确认开始提取? (y/n)", default="y")
    if confirm.lower() != 'y':
        print("⚠️  已取消")
        return

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ 错误：无法打开视频文件")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"\n📊 视频信息:")
        print(f"   总帧数: {total_frames if total_frames > 0 else '未知'}")
        print(f"   帧率: {fps:.2f} fps")
        print(f"   分辨率: {width}x{height}")
        print(f"\n🚀 开始提取帧（每 {group_size} 帧一组）...\n")

        os.makedirs(output_base, exist_ok=True)
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            group_index = (frame_count - 1) // group_size + 1
            group_folder = os.path.join(output_base, f"part{group_index}")
            os.makedirs(group_folder, exist_ok=True)

            filename = f"{frame_count}.{img_format}"
            filepath = os.path.join(group_folder, filename)

            success = cv2.imwrite(filepath, frame)
            if success:
                saved_count += 1
                if frame_count % 100 == 0:
                    if total_frames > 0:
                        pct = frame_count / total_frames * 100
                        print(f"   ✅ 已处理: {frame_count}/{total_frames} 帧 ({pct:.1f}%) [组: part{group_index}]")
                    else:
                        print(f"   ✅ 已处理: {frame_count} 帧 [组: part{group_index}]")
            else:
                print(f"   ❌ 警告：保存第 {frame_count} 帧失败")

        cap.release()

        print(f"\n{'='*50}")
        print("✅ 提取完成！")
        print(f"   成功提取: {saved_count} 帧")
        print(f"   保存位置: {os.path.abspath(output_base)}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"\n❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()

# ========== 2. 批量缩放图片功能 ==========
def batch_resize_images():
    print("\n" + "=" * 60)
    print("  🖼️  批量缩放图片 (Batch Resize)")
    print("=" * 60)

    if not PIL_AVAILABLE:
        print("❌ 错误：未安装 Pillow (PIL)")
        print("请运行: pip install pillow")
        return

    print("\n📂 请选择输入方式:")
    print("  [1] 处理 frame_extract 生成的分组文件夹 (part1, part2...)")
    print("  [2] 处理单个文件夹内的所有图片")
    choice = get_input("选择", default="1")

    input_path = get_input("请输入文件夹路径").strip('"').strip("'")
    input_path = Path(input_path).expanduser().resolve()

    if not input_path.exists() or not input_path.is_dir():
        print(f"❌ 错误：路径不存在或不是文件夹 - {input_path}")
        return

    # 获取图片文件
    image_files = []
    if choice == "1":
        # 分组模式
        part_dirs = []
        for item in input_path.iterdir():
            if item.is_dir() and re.match(r'^part\d+', item.name, re.IGNORECASE):
                files = list(item.glob("*.png")) + list(item.glob("*.jpg")) + list(item.glob("*.jpeg"))
                if files:
                    files = sorted(files, key=lambda s: [int(c) if c.isdigit() else c.lower() 
                                                         for c in re.split(r'(\d+)', str(s))])
                    part_dirs.append((item, files))

        if not part_dirs:
            print("⚠️  未找到有效的 part* 子文件夹")
            return

        part_dirs.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() 
                                      for c in re.split(r'(\d+)', x[0].name)])
        print(f"✅ 找到 {len(part_dirs)} 个分组文件夹")
        for d, files in part_dirs:
            print(f"   - {d.name} ({len(files)} 张图片)")
    else:
        # 单文件夹模式
        files = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg")) + list(input_path.glob("*.jpeg"))
        if not files:
            print("❌ 未找到图片文件")
            return
        image_files = sorted(files, key=lambda s: [int(c) if c.isdigit() else c.lower() 
                                                   for c in re.split(r'(\d+)', str(s))])
        print(f"✅ 找到 {len(image_files)} 张图片")
        part_dirs = [(input_path, image_files)]

    # 选择缩放模式
    print("\n🎯 请选择缩放模式:")
    print("  [1] 指定宽度，高度自动等比例")
    print("  [2] 指定高度，宽度自动等比例")
    print("  [3] 强制指定宽高 (可能变形)")
    print("  [4] 指定缩放百分比 (如 50% 为原图一半)")

    mode_choice = get_input("选择", default="1")

    resize_params = {}
    if mode_choice == "1":
        width = get_input("目标宽度 (像素)", input_type=int, validator=lambda x: (x > 0, "宽度必须大于0"))
        resize_params = {'mode': 'width', 'width': width, 'desc': f"等比例缩放，宽度 {width}px"}
    elif mode_choice == "2":
        height = get_input("目标高度 (像素)", input_type=int, validator=lambda x: (x > 0, "高度必须大于0"))
        resize_params = {'mode': 'height', 'height': height, 'desc': f"等比例缩放，高度 {height}px"}
    elif mode_choice == "3":
        width = get_input("目标宽度 (像素)", input_type=int, validator=lambda x: (x > 0, "宽度必须大于0"))
        height = get_input("目标高度 (像素)", input_type=int, validator=lambda x: (x > 0, "高度必须大于0"))
        resize_params = {'mode': 'fixed', 'width': width, 'height': height, 'desc': f"强制缩放至 {width}x{height}"}
    elif mode_choice == "4":
        percent = get_input("缩放百分比 (如 50)", input_type=float, validator=lambda x: (x > 0, "百分比必须大于0"))
        resize_params = {'mode': 'percent', 'percent': percent, 'desc': f"缩放至原图 {percent}%"}
    else:
        print("❌ 无效选择")
        return

    # 输出路径
    base_name = input_path.name
    script_dir = Path(__file__).parent.resolve()
    default_output = script_dir / f"{base_name}_resized"
    output_base = get_input("输出目录", default=str(default_output))
    output_base = Path(output_base.strip('"').strip("'"))

    print(f"\n{'-'*50}")
    print("📋 处理摘要:")
    print(f"   输入: {input_path}")
    print(f"   输出: {output_base}")
    print(f"   模式: {resize_params['desc']}")
    if choice == "1":
        print(f"   分组数: {len(part_dirs)}")
    print(f"{'-'*50}")

    confirm = get_input("确认开始处理? (y/n)", default="y")
    if confirm.lower() != 'y':
        print("⚠️  已取消")
        return

    # 开始处理
    try:
        total_success = 0
        total_fail = 0

        for part_dir, files in part_dirs:
            if choice == "1":
                rel_name = part_dir.name
                output_dir = output_base / rel_name
            else:
                output_dir = output_base

            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n📦 处理 {part_dir.name if choice == '1' else input_path.name} ({len(files)} 张)...")

            for i, file_path in enumerate(files, 1):
                output_file = output_dir / file_path.name

                try:
                    img = Image.open(file_path)
                    orig_w, orig_h = img.size

                    # 计算新尺寸
                    if resize_params['mode'] == 'width':
                        new_w = resize_params['width']
                        new_h = int(orig_h * (new_w / orig_w))
                    elif resize_params['mode'] == 'height':
                        new_h = resize_params['height']
                        new_w = int(orig_w * (new_h / orig_h))
                    elif resize_params['mode'] == 'fixed':
                        new_w, new_h = resize_params['width'], resize_params['height']
                    elif resize_params['mode'] == 'percent':
                        p = resize_params['percent'] / 100
                        new_w, new_h = int(orig_w * p), int(orig_h * p)

                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # 保存
                    ext = file_path.suffix.lower()
                    if ext in ['.jpg', '.jpeg']:
                        resized.save(output_file, 'JPEG', quality=95, optimize=True)
                    elif ext == '.png':
                        resized.save(output_file, 'PNG', optimize=True, compress_level=9)
                    else:
                        resized.save(output_file)

                    total_success += 1
                    if i % 10 == 0 or i == len(files):
                        print(f"   ✅ [{i}/{len(files)}] {file_path.name} → {new_w}x{new_h}")

                except Exception as e:
                    total_fail += 1
                    print(f"   ❌ [{i}/{len(files)}] {file_path.name} - {e}")

        print(f"\n{'='*50}")
        print("📊 全部处理完成!")
        print(f"   ✅ 成功: {total_success}")
        print(f"   ❌ 失败: {total_fail}")
        print(f"   📁 输出位置: {output_base}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

# ========== 3. 单张图片模式 ==========
def image_to_adofai():
    print("\n" + "=" * 60)
    print("  单张图片转 ADOFAI")
    print("=" * 60)

    img_path = get_input("请输入图片路径")
    if not os.path.exists(img_path):
        print(f" 图片不存在: {img_path}")
        return

    script_dir = Path(__file__).parent.resolve()
    default_name = f"{Path(img_path).stem}.adofai"
    out_input = input(f"请输入输出文件名（直接回车使用 {default_name}）: ").strip()
    if not out_input:
        out_input = default_name
    if not out_input.endswith('.adofai'):
        out_input += '.adofai'

    output_path = Path(out_input)
    if not output_path.is_absolute():
        output_path = script_dir / output_path

    y_offset = get_input(
        "Y轴偏移量（正数，控制行间距）",
        default=0.9,
        input_type=float,
        validator=lambda x: (x > 0, "Y轴偏移必须大于0")
    )

    print("\n" + "-" * 50)
    print("确认设置:")
    print(f"  输入图片: {img_path}")
    print(f"  输出文件: {output_path}")
    print(f"  Y偏移: {y_offset}")
    print("-" * 50)
    confirm = get_input("\n开始生成? (y/n)", default="y")
    if confirm.lower() != 'y':
        print("  ⚠️ 取消操作")
        return

    try:
        print("\n正在生成 ADOFAI 关卡...")
        generate_adofai(img_path, str(output_path), y_offset=y_offset)
        print("\n生成成功！")
        print(f"  输出: {output_path}")
    except Exception as e:
        print(f"\n生成失败: {e}")
        import traceback
        traceback.print_exc()

# ========== 4. 单文件夹模式 ==========
def get_frame_files():
    print("\n--- 选择帧文件 ---")
    print("请选择输入方式:")
    print("  [1] 输入文件夹路径（自动读取所有图片）")
    print("  [2] 输入通配符模式（如: frames/*.png）")
    print("  [3] 手动输入文件列表")
    choice = get_input("选择", default="1")
    frame_paths = []
    if choice == "1":
        folder = get_input("请输入帧文件夹路径")
        if not os.path.isdir(folder):
            print(f"   文件夹不存在: {folder}")
            return None
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
        for ext in extensions:
            pattern = os.path.join(folder, ext)
            frame_paths.extend(glob.glob(pattern))
        if not frame_paths:
            print(f" 文件夹中没有找到图片文件")
            return None
        print(f"   找到 {len(frame_paths)} 个图片文件")
    elif choice == "2":
        pattern = get_input("请输入通配符模式（如: frames/*.png）")
        frame_paths = glob.glob(pattern)
        if not frame_paths:
            print(f"没有匹配到任何文件")
            return None
        print(f"  ✓ 找到 {len(frame_paths)} 个文件")
    elif choice == "3":
        print("请输入帧文件路径，每行一个，输入空行结束:")
        while True:
            path = input("  文件路径: ").strip()
            if not path:
                break
            if not os.path.exists(path):
                print(f" 文件不存在: {path}")
                continue
            frame_paths.append(path)
        if not frame_paths:
            print("  没有输入任何文件")
            return None
    else:
        print("  无效的选择")
        return None

    frame_paths = sorted(frame_paths, key=natural_sort_key)
    print("\n文件列表预览（前5个）:")
    for i, path in enumerate(frame_paths[:5]):
        print(f"  {i+1}. {os.path.basename(path)}")
    if len(frame_paths) > 5:
        print(f"  ... 还有 {len(frame_paths) - 5} 个文件")
    confirm = get_input("\n确认使用这些文件? (y/n)", default="y")
    if confirm.lower() != 'y':
        return None
    return frame_paths

def single_to_adofai():
    print("\n" + "=" * 60)
    print("  单文件夹帧转 ADOFAI")
    print("=" * 60)
    frame_paths = get_frame_files()
    if not frame_paths:
        return

    script_dir = Path(__file__).parent.resolve()
    default_output = script_dir / "output.adofai"
    output_path = get_input("输出文件路径（.adofai）", default=str(default_output))
    if not output_path.endswith('.adofai'):
        output_path += '.adofai'

    fps = get_input(
        "FPS（帧率）",
        default=DEFAULT_FPS,
        input_type=float,
        validator=lambda x: (x > 0, "FPS必须大于0")
    )
    zoom = get_input(
        "Zoom（缩放百分比）",
        default=DEFAULT_ZOOM,
        input_type=int,
        validator=lambda x: (x > 0, "Zoom必须大于0")
    )

    print("\n" + "-" * 50)
    print("确认设置:")
    print(f"  帧数: {len(frame_paths)}")
    print(f"  输出: {output_path}")
    print(f"  FPS: {fps} → BPM: {int(fps * 60)}")
    print(f"  Zoom: {zoom}%")
    print("-" * 50)
    confirm = get_input("\n开始生成? (y/n)", default="y")
    if confirm.lower() != 'y':
        return

    try:
        generate_video_adofai(frame_paths, output_path, fps, zoom)
        print("\n生成成功！")
        print(f"  输出: {output_path}")
    except Exception as e:
        print(f"\n生成失败: {e}")
        import traceback
        traceback.print_exc()

# ========== 5. 分组模式 ==========
def get_grouped_parts(input_folder):
    input_path = Path(input_folder)
    if not input_path.is_dir():
        return None
    part_dirs = []
    for item in input_path.iterdir():
        if item.is_dir() and re.match(r'^part\d+$', item.name, re.IGNORECASE):
            files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
                files.extend(glob.glob(str(item / ext)))
            if files:
                files = sorted(files, key=natural_sort_key)
                part_dirs.append((item.name, files))
    if not part_dirs:
        return None
    part_dirs.sort(key=lambda x: natural_sort_key(x[0]))
    return part_dirs

def grouped_to_adofai():
    print("\n" + "=" * 60)
    print("  分组帧转 ADOFAI（part1, part2...）")
    print("=" * 60)

    input_folder = get_input("请输入 frame_extract 生成的顶层文件夹路径（如 test）")
    input_folder = input_folder.strip('"').strip("'")
    part_dirs = get_grouped_parts(input_folder)
    if not part_dirs:
        print("  未找到有效 part* 子文件夹")
        return

    base_name = Path(input_folder).name
    script_dir = Path(__file__).parent.resolve()
    output_parent = script_dir / f"{base_name}_levels"
    output_parent.mkdir(parents=True, exist_ok=True)

    fps = get_input(
        "FPS（帧率）",
        default=DEFAULT_FPS,
        input_type=float,
        validator=lambda x: (x > 0, "FPS必须大于0")
    )
    zoom = get_input(
        "Zoom（缩放百分比）",
        default=DEFAULT_ZOOM,
        input_type=int,
        validator=lambda x: (x > 0, "Zoom必须大于0")
    )

    print("\n" + "-" * 50)
    print("确认设置:")
    print(f"  输入: {input_folder}")
    print(f"  输出: {output_parent}")
    print(f"  分组数: {len(part_dirs)}")
    print(f"  FPS: {fps} → BPM: {int(fps * 60)}")
    print(f"  Zoom: {zoom}%")
    print("-" * 50)
    confirm = get_input("\n开始生成? (y/n)", default="y")
    if confirm.lower() != 'y':
        return

    success = 0
    for part_name, frames in part_dirs:
        out_file = output_parent / f"{part_name}.adofai"
        try:
            print(f"  处理 {part_name} ({len(frames)} 帧)...")
            generate_video_adofai(frames, str(out_file), fps, zoom)
            print(f"    ✅ {part_name}.adofai")
            success += 1
        except Exception as e:
            print(f"    ❌ {part_name}.adofai - {e}")
    print(f"\n 完成！成功生成 {success}/{len(part_dirs)} 个关卡")

# ========== 主循环 ==========
def main():
    print_header()
    while True:
        print_menu()
        choice = get_input("请选择", default="1")
        if choice == "1":
            extract_video_frames()
        elif choice == "2":
            batch_resize_images()
        elif choice == "3":
            single_to_adofai()
        elif choice == "4":
            grouped_to_adofai()
        elif choice == "5":
            image_to_adofai()
        elif choice == "0":
            print("\n👋 再见！")
            sys.exit(0)
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)