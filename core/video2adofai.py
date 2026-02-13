#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频帧转ADOFAI模块（合并v1/v2版本）
- v1: ColorTrack方案（每帧独立轨道，适合小视频）
- v2: RecolorTrack方案（共享轨道，更高效）
"""

import os
import sys
import glob

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import natural_sort_key, format_value, pixel_to_hex, print_progress, print_progress_inline
from config import (
    get_adofai_settings,
    DEFAULT_FPS, DEFAULT_ZOOM, ROW_OFFSET,
    FRAME_START_Y_OFFSET, FRAME_GAP, FLOOR_WIDTH, FLOOR_HEIGHT
)


def generate_video_adofai(frame_paths, output_path, fps=None, zoom=None, verbose=True):
    """
    将视频帧序列转换为ADOFAI关卡文件（v1 ColorTrack方案）
    
    参数:
        frame_paths: 帧图片路径列表
        output_path: 输出.adofai文件路径
        fps: 帧率（默认从config读取）
        zoom: 缩放百分比（默认从config读取）
        verbose: 是否显示详细信息
    
    返回:
        bool: 是否成功
    """
    if not PIL_AVAILABLE:
        raise ImportError("需要安装 Pillow: pip install Pillow")
    
    if fps is None:
        fps = DEFAULT_FPS
    if zoom is None:
        zoom = DEFAULT_ZOOM
    
    try:
        # 读取所有帧
        if verbose:
            print(f"读取 {len(frame_paths)} 帧图片...")
        frames = []
        for i, path in enumerate(frame_paths):
            img = Image.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            frames.append(img)
            if verbose:
                print_progress(i + 1, len(frame_paths), prefix="  读取帧", suffix="")
        
        # 检查所有帧尺寸是否一致
        width, height = frames[0].size
        for i, frame in enumerate(frames[1:], 1):
            if frame.size != (width, height):
                raise ValueError(f"帧 {i+1} 的尺寸 {frame.size} 与第一帧 {(width, height)} 不一致")
        
        num_frames = len(frames)
        pixels_per_frame = width * height
        
        # 计算BPM
        bpm = int(fps * 60)
        
        # 计算总Floor数
        total_floors = num_frames + (num_frames * pixels_per_frame) + 1
        
        if verbose:
            print(f"\n视频信息:")
            print(f"  帧数: {num_frames}")
            print(f"  分辨率: {width}×{height}")
            print(f"  每帧像素: {pixels_per_frame}")
            print(f"  FPS: {fps}")
            print(f"  BPM: {bpm}")
            print(f"  Zoom: {zoom}%")
            print(f"\n关卡统计:")
            print(f"  Director区: {num_frames} 个Floor")
            print(f"  Frame区: {num_frames * pixels_per_frame} 个Floor")
            print(f"  总Floor数: {total_floors}")
        
        # 开始生成
        lines = []
        lines.append("{")
        
        # angleData
        angle_count = total_floors - 1
        angles = ", ".join(["0"] * angle_count)
        lines.append(f'\t"angleData": [{angles}], ')
        
        # settings
        lines.append('\t"settings":')
        lines.append('\t{')
        
        settings = get_adofai_settings(
            level_desc=f"Video {width}×{height} {fps}FPS {num_frames}frames",
            level_tags="video",
            bpm=bpm,
            zoom=zoom,
            track_color="000000"
        )
        
        for i, (key, val) in enumerate(settings):
            comma = "," if i < len(settings) - 1 else ""
            lines.append(f'\t\t"{key}": {format_value(val)}{comma}')
        
        lines.append('\t},')
        
        # actions
        lines.append('\t"actions":')
        lines.append('\t[')
        
        actions = []
        
        if verbose:
            print("\n生成Director区...")
        
        # Director区: Floor 1 到 Floor num_frames
        for frame_idx in range(num_frames):
            floor = frame_idx + 1
            
            frame_y_start = FRAME_START_Y_OFFSET - frame_idx * (height * FLOOR_HEIGHT + FRAME_GAP)
            camera_x = width / 2
            camera_y = frame_y_start - (height * FLOOR_HEIGHT) / 2
            
            move_camera = (floor, f'\t\t{{ "floor": {floor}, "eventType": "MoveCamera", "duration": 0, "relativeTo": "Global", "position": [{camera_x}, {camera_y}], "zoom": {zoom}, "angleOffset": 0, "ease": "Linear", "dontDisable": false, "minVfxOnly": false, "eventTag": ""}}')
            actions.append(move_camera)
            
            if verbose and ((frame_idx + 1) % 10 == 0 or frame_idx == num_frames - 1):
                print(f"  Director Floor {floor}: 帧{frame_idx+1} 中心=({camera_x:.1f}, {camera_y:.1f})")
        
        if verbose:
            print("\n生成Frame区...")
        
        # Frame区: 从 Floor (num_frames + 1) 开始
        current_floor = num_frames + 1
        total_pixels = num_frames * pixels_per_frame
        processed_pixels = 0
        
        for frame_idx in range(num_frames):
            pixels = list(frames[frame_idx].getdata())
            
            for pixel_idx in range(pixels_per_frame):
                floor = current_floor
                current_floor += 1
                processed_pixels += 1
                
                hex_color = pixel_to_hex(*pixels[pixel_idx])
                
                # ColorTrack事件
                color_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "ColorTrack", "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Minimal", "trackTexture": "", "trackTextureScale": 1, "trackGlowIntensity": 100, "justThisTile": false}}')
                actions.append(color_action)
                
                # PositionTrack逻辑
                if frame_idx == 0 and pixel_idx == 0:
                    x_offset = -(num_frames + 1)
                    y_offset = FRAME_START_Y_OFFSET
                    pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                    actions.append(pos_action)
                
                elif pixel_idx == 0 and frame_idx > 0:
                    x_offset = -width
                    y_offset = -(ROW_OFFSET + FRAME_GAP)
                    pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                    actions.append(pos_action)
                
                else:
                    col = pixel_idx % width
                    
                    if col == 0 and pixel_idx > 0:
                        x_offset = -width
                        y_offset = -ROW_OFFSET
                        pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                        actions.append(pos_action)
            
            # 每帧结束后更新进度
            if verbose:
                print_progress(processed_pixels, total_pixels, prefix="  生成像素", suffix=f"帧{frame_idx+1}/{num_frames}")
        
        # 按floor编号排序
        actions.sort(key=lambda x: x[0])
        
        if verbose:
            print("\n写入actions...")
        
        for i, (_, action_str) in enumerate(actions):
            if i < len(actions) - 1:
                lines.append(action_str + ",")
            else:
                lines.append(action_str)
        
        lines.append('\t],')
        
        # decorations
        lines.append('\t"decorations":')
        lines.append('\t[')
        lines.append('\t]')
        
        lines.append("}")
        
        # 写入文件
        if verbose:
            print(f"\n写入文件: {output_path}")
        
        content = "\n".join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if verbose:
            print(f"\n✓ 成功生成 ADOFAI 视频关卡!")
            print(f"  输出文件: {output_path}")
            print(f"  总事件数: {len(actions)}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"错误: 找不到文件 '{e.filename}'")
        return False
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_video_adofai_v2(frame_paths, output_path, fps=None, zoom=None, verbose=True):
    """
    使用RecolorTrack方案生成视频ADOFAI（v2高效版本）
    
    参数:
        frame_paths: 帧图片路径列表
        output_path: 输出.adofai文件路径
        fps: 帧率（默认从config读取）
        zoom: 缩放百分比（默认从config读取）
        verbose: 是否显示详细信息
    
    返回:
        bool: 是否成功
    """
    if not PIL_AVAILABLE:
        raise ImportError("需要安装 Pillow: pip install Pillow")
    
    if fps is None:
        fps = DEFAULT_FPS
    if zoom is None:
        zoom = DEFAULT_ZOOM
    
    try:
        # 读取所有帧
        if verbose:
            print(f"读取 {len(frame_paths)} 帧图片...")
        frames = []
        for i, path in enumerate(frame_paths):
            img = Image.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            frames.append(img)
            if verbose:
                print_progress(i + 1, len(frame_paths), prefix="  读取帧", suffix="")
        
        # 检查所有帧尺寸是否一致
        width, height = frames[0].size
        for i, frame in enumerate(frames[1:], 1):
            if frame.size != (width, height):
                raise ValueError(f"帧 {i+1} 的尺寸 {frame.size} 与第一帧 {(width, height)} 不一致")
        
        num_frames = len(frames)
        pixels_per_frame = width * height
        position_value = [width / 2, -height / 2]
        
        # BPM固定为60
        bpm = 60
        
        # 角度间隔公式：d = 3 × BPM / fps
        d = 3 * bpm / fps
        
        if verbose:
            print(f"\n视频信息:")
            print(f"  帧数: {num_frames}")
            print(f"  分辨率: {width}×{height}")
            print(f"  每帧像素: {pixels_per_frame}")
            print(f"  FPS: {fps}")
            print(f"  BPM: {bpm} (固定)")
            print(f"  角度间隔 d: {d}")
            print(f"  Zoom: {zoom}%")
        
        # 砖块数 = 一帧的像素数
        total_floors = pixels_per_frame
        
        if verbose:
            print(f"\n关卡统计:")
            print(f"  砖块数: {total_floors}")
            print(f"  RecolorTrack数量: {num_frames} × {pixels_per_frame} = {num_frames * pixels_per_frame}")
        
        # 开始生成
        lines = []
        lines.append("{")
        
        # angleData: 全0
        angles = ", ".join(["0"] * total_floors)
        lines.append(f'\t"angleData": [{angles}], ')
        
        # settings
        lines.append('\t"settings":')
        lines.append('\t{')
        
        settings = get_adofai_settings(
            level_desc="Video",
            level_tags="video",
            bpm=bpm,
            zoom=zoom,
            track_color="000000",
            position=position_value,
            relative_to="Global"
        )
        
        for i, (key, val) in enumerate(settings):
            comma = "," if i < len(settings) - 1 else ""
            lines.append(f'\t\t"{key}": {format_value(val)}{comma}')
        
        lines.append('\t},')
        
        # actions
        lines.append('\t"actions":')
        lines.append('\t[')
        
        if verbose:
            print("\n生成RecolorTrack...")
        
        # 收集Floor 1的RecolorTrack
        floor1_actions = []
        total_recolor = num_frames * pixels_per_frame
        
        for frame_idx in range(num_frames):
            angle_offset = frame_idx * d
            pixels = list(frames[frame_idx].getdata())
            
            for pixel_idx in range(pixels_per_frame):
                tile_index = pixel_idx + 1
                hex_color = pixel_to_hex(*pixels[pixel_idx])
                
                floor1_actions.append(f'\t\t{{ "floor": 1, "eventType": "RecolorTrack", "startTile": [{tile_index}, "Start"], "endTile": [{tile_index}, "Start"], "gapLength": 0, "duration": 0, "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Basic", "trackGlowIntensity": 100, "angleOffset": {angle_offset}, "ease": "Linear", "eventTag": ""}}')
            
            # 每帧结束后更新进度
            if verbose:
                current_count = (frame_idx + 1) * pixels_per_frame
                print_progress(current_count, total_recolor, prefix="  生成RecolorTrack", suffix=f"帧{frame_idx+1}/{num_frames}")
        
        if verbose:
            print("\n生成PositionTrack（换行）...")
        
        # 收集其他Floor的PositionTrack
        other_actions = {}
        
        for floor in range(2, total_floors + 1):
            pixel_idx = floor - 1
            col = pixel_idx % width
            
            if col == 0 and floor < total_floors:
                x_offset = -width
                y_offset = -ROW_OFFSET
                other_actions[floor] = f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}'
        
        if verbose:
            print(f"\n写入文件: {output_path}")
            print(f"  RecolorTrack数: {len(floor1_actions)}")
            print(f"  PositionTrack数: {len(other_actions)}")
        
        # 直接写入文件（流式写入）
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入前面部分
            f.write("\n".join(lines))
            f.write("\n")
            
            # 写入Floor 1的所有RecolorTrack
            for i, action in enumerate(floor1_actions):
                f.write(action)
                if i < len(floor1_actions) - 1 or other_actions:
                    f.write(",\n")
                else:
                    f.write("\n")
            
            # 写入其他Floor的PositionTrack（按floor排序）
            sorted_floors = sorted(other_actions.keys())
            for i, floor in enumerate(sorted_floors):
                f.write(other_actions[floor])
                if i < len(sorted_floors) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")
            
            # 写入结尾
            f.write('\t],\n')
            f.write('\t"decorations":\n')
            f.write('\t[\n')
            f.write('\t]\n')
            f.write("}")
        
        if verbose:
            print(f"\n✓ 成功生成 ADOFAI 视频关卡!")
            print(f"  输出文件: {output_path}")
            print(f"  砖块数: {total_floors}")
            print(f"  总事件数: {len(floor1_actions) + len(other_actions)}")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='视频帧序列转 ADOFAI 关卡')
    parser.add_argument('frames', nargs='+', help='帧图片文件路径（支持通配符）')
    parser.add_argument('-o', '--output', required=True, help='输出 .adofai 文件路径')
    parser.add_argument('--fps', type=float, default=DEFAULT_FPS, help=f'帧率（默认 {DEFAULT_FPS}）')
    parser.add_argument('--zoom', type=int, default=DEFAULT_ZOOM, help=f'缩放百分比（默认 {DEFAULT_ZOOM}）')
    parser.add_argument('--v2', action='store_true', help='使用v2 RecolorTrack方案（更高效）')
    
    args = parser.parse_args()
    
    # 处理通配符
    frame_paths = []
    for pattern in args.frames:
        if '*' in pattern or '?' in pattern:
            matched = glob.glob(pattern)
            frame_paths.extend(sorted(matched, key=natural_sort_key))
        else:
            frame_paths.append(pattern)
    
    # 自然排序
    frame_paths = sorted(frame_paths, key=natural_sort_key)
    
    if not frame_paths:
        print("错误: 没有找到任何帧图片文件")
        sys.exit(1)
    
    if args.fps <= 0:
        print(f"错误: FPS必须大于0，当前值: {args.fps}")
        sys.exit(1)
    
    print(f"找到 {len(frame_paths)} 个帧文件")
    
    if args.v2:
        success = generate_video_adofai_v2(frame_paths, args.output, args.fps, args.zoom)
    else:
        success = generate_video_adofai(frame_paths, args.output, args.fps, args.zoom)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
