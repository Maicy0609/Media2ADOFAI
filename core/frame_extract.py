#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频提取帧模块
"""

import os
from pathlib import Path

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def extract_frames(video_path, output_base_dir=None, image_format='png', group_size=1000, verbose=True):
    """
    从视频中提取帧并分组保存
    
    参数:
        video_path: 视频文件路径
        output_base_dir: 输出基础目录（默认使用视频文件名创建目录）
        image_format: 图片格式（png/jpg，默认png）
        group_size: 每组帧数（默认1000）
        verbose: 是否显示进度信息
    
    返回:
        dict: {'success': bool, 'frame_count': int, 'output_dir': str, 'error': str or None}
    """
    if not CV2_AVAILABLE:
        return {
            'success': False,
            'frame_count': 0,
            'output_dir': None,
            'error': '需要安装 opencv-python: pip install opencv-python'
        }
    
    if not os.path.exists(video_path):
        return {
            'success': False,
            'frame_count': 0,
            'output_dir': None,
            'error': f'视频文件不存在: {video_path}'
        }
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    if output_base_dir is None:
        output_base_dir = os.path.dirname(os.path.abspath(video_path))
    
    top_dir = os.path.join(output_base_dir, video_name)
    os.makedirs(top_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            'success': False,
            'frame_count': 0,
            'output_dir': None,
            'error': '无法打开视频文件'
        }
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if verbose:
        print(f"\n视频信息:")
        print(f"  总帧数: {total_frames if total_frames > 0 else '未知'}")
        print(f"  帧率: {fps:.2f} fps")
        print(f"  分辨率: {width}x{height}")
        print(f"\n开始提取帧（每 {group_size} 帧一组）...\n")
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        group_index = (frame_count - 1) // group_size + 1
        group_folder = os.path.join(top_dir, f"part{group_index}")
        os.makedirs(group_folder, exist_ok=True)
        
        filename = f"{frame_count}.{image_format}"
        filepath = os.path.join(group_folder, filename)
        
        success = cv2.imwrite(filepath, frame)
        if success:
            saved_count += 1
            if verbose and frame_count % 100 == 0:
                if total_frames > 0:
                    pct = frame_count / total_frames * 100
                    print(f"  已处理: {frame_count}/{total_frames} 帧 ({pct:.1f}%) [当前组: part{group_index}]")
                else:
                    print(f"  已处理: {frame_count} 帧 [当前组: part{group_index}]")
    
    cap.release()
    
    if verbose:
        print(f"\n✅ 完成！")
        print(f"  成功提取: {saved_count} 帧")
        print(f"  保存位置: {os.path.abspath(top_dir)}")
    
    return {
        'success': True,
        'frame_count': saved_count,
        'output_dir': os.path.abspath(top_dir),
        'error': None
    }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='视频提取帧工具')
    parser.add_argument('video', help='输入视频文件路径')
    parser.add_argument('-o', '--output', help='输出目录（默认使用视频名创建目录）')
    parser.add_argument('-f', '--format', default='png', choices=['png', 'jpg', 'jpeg', 'bmp'],
                       help='输出图片格式（默认png）')
    parser.add_argument('-g', '--group', type=int, default=1000,
                       help='每组帧数（默认1000）')
    
    args = parser.parse_args()
    
    result = extract_frames(
        video_path=args.video,
        output_base_dir=args.output,
        image_format=args.format,
        group_size=args.group,
        verbose=True
    )
    
    if not result['success']:
        print(f"❌ 错误: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()
