#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 命令行入口
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    extract_frames,
    batch_resize,
    generate_image_adofai,
    generate_video_adofai,
    generate_video_adofai_v2
)
from utils import natural_sort_key, find_image_files
from config import DEFAULT_FPS, DEFAULT_ZOOM, DEFAULT_Y_OFFSET


def cmd_extract_frames(args):
    """视频提取帧命令"""
    result = extract_frames(
        video_path=args.video,
        output_base_dir=args.output,
        image_format=args.format,
        group_size=args.group,
        verbose=True
    )
    if not result['success']:
        print(f"❌ 错误: {result['error']}")
        sys.exit(1)


def cmd_resize(args):
    """批量缩放图片命令"""
    # 确定模式
    if args.width:
        mode, w, h, p = 'width', args.width, 0, 0
    elif args.height:
        mode, w, h, p = 'height', 0, args.height, 0
    elif args.fixed:
        mode, w, h, p = 'fixed', args.fixed[0], args.fixed[1], 0
    elif args.percent:
        mode, w, h, p = 'percent', 0, 0, args.percent
    else:
        print("错误: 请指定缩放模式")
        sys.exit(1)
    
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


def cmd_image2adofai(args):
    """图片转ADOFAI命令"""
    try:
        success = generate_image_adofai(
            image_path=args.image,
            output_path=args.output,
            y_offset=args.y_offset
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


def cmd_video2adofai(args):
    """视频帧转ADOFAI命令"""
    import glob
    
    # 处理通配符
    frame_paths = []
    for pattern in args.frames:
        if '*' in pattern or '?' in pattern:
            matched = glob.glob(pattern)
            frame_paths.extend(sorted(matched, key=natural_sort_key))
        else:
            frame_paths.append(pattern)
    
    frame_paths = sorted(frame_paths, key=natural_sort_key)
    
    if not frame_paths:
        print("错误: 没有找到任何帧图片文件")
        sys.exit(1)
    
    print(f"找到 {len(frame_paths)} 个帧文件")
    
    if args.v2:
        success = generate_video_adofai_v2(frame_paths, args.output, args.fps, args.zoom)
    else:
        success = generate_video_adofai(frame_paths, args.output, args.fps, args.zoom)
    
    if not success:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='ADOFAI 工具集 - 将图片或视频转换成ADOFAI关卡文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 视频提取帧
  python cli.py extract video.mp4 -o ./frames -g 1000

  # 批量缩放图片
  python cli.py resize ./frames ./resized -W 120

  # 图片转ADOFAI
  python cli.py image2adofai image.png -o output.adofai

  # 视频帧转ADOFAI (v1)
  python cli.py video2adofai ./frames/*.png -o output.adofai --fps 5

  # 视频帧转ADOFAI (v2高效版)
  python cli.py video2adofai ./frames/*.png -o output.adofai --v2
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # extract 命令
    extract_parser = subparsers.add_parser('extract', help='视频提取帧')
    extract_parser.add_argument('video', help='输入视频文件路径')
    extract_parser.add_argument('-o', '--output', help='输出目录')
    extract_parser.add_argument('-f', '--format', default='png', choices=['png', 'jpg', 'jpeg', 'bmp'],
                               help='输出图片格式（默认png）')
    extract_parser.add_argument('-g', '--group', type=int, default=1000,
                               help='每组帧数（默认1000）')
    extract_parser.set_defaults(func=cmd_extract_frames)
    
    # resize 命令
    resize_parser = subparsers.add_parser('resize', help='批量缩放图片')
    resize_parser.add_argument('input', help='输入文件夹路径')
    resize_parser.add_argument('output', help='输出文件夹路径')
    
    resize_group = resize_parser.add_mutually_exclusive_group(required=True)
    resize_group.add_argument('-W', '--width', type=int, help='指定宽度，高度等比例')
    resize_group.add_argument('-H', '--height', type=int, help='指定高度，宽度等比例')
    resize_group.add_argument('-F', '--fixed', nargs=2, type=int, metavar=('W', 'H'),
                             help='强制指定宽高')
    resize_group.add_argument('-P', '--percent', type=float, help='缩放百分比')
    
    resize_parser.add_argument('--no-group', action='store_true',
                              help='非分组模式')
    resize_parser.set_defaults(func=cmd_resize)
    
    # image2adofai 命令
    img_parser = subparsers.add_parser('image2adofai', help='图片转ADOFAI')
    img_parser.add_argument('image', help='输入图片路径')
    img_parser.add_argument('-o', '--output', help='输出 .adofai 文件路径')
    img_parser.add_argument('-y', '--y-offset', type=float, default=DEFAULT_Y_OFFSET,
                           help=f'Y轴偏移量（默认{DEFAULT_Y_OFFSET}）')
    img_parser.set_defaults(func=cmd_image2adofai)
    
    # video2adofai 命令
    vid_parser = subparsers.add_parser('video2adofai', help='视频帧转ADOFAI')
    vid_parser.add_argument('frames', nargs='+', help='帧图片文件路径（支持通配符）')
    vid_parser.add_argument('-o', '--output', required=True, help='输出 .adofai 文件路径')
    vid_parser.add_argument('--fps', type=float, default=DEFAULT_FPS,
                           help=f'帧率（默认{DEFAULT_FPS}）')
    vid_parser.add_argument('--zoom', type=int, default=DEFAULT_ZOOM,
                           help=f'缩放百分比（默认{DEFAULT_ZOOM}）')
    vid_parser.add_argument('--v2', action='store_true',
                           help='使用v2 RecolorTrack方案（更高效）')
    vid_parser.set_defaults(func=cmd_video2adofai)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
