# ==================== CONFIG ====================
# 视频转ADOFAI配置区

# 帧渲染起始位置（相对于Director区）
FRAME_START_Y_OFFSET = -10  # Director Y坐标 + 这个偏移 = 帧区起始Y坐标

# 帧间距离（每帧之间的垂直间距）
FRAME_GAP = 10  # 相对坐标中的Y偏移

# 行间距（帧内每行之间的垂直间距）
ROW_OFFSET = 0.9  # 相对坐标中的Y偏移

# Floor尺寸（游戏引擎固定值，不建议修改）
FLOOR_WIDTH = 1
FLOOR_HEIGHT = 0.9

# 默认参数
DEFAULT_FPS = 5
DEFAULT_ZOOM = 100

# ================================================

import json
from PIL import Image
import argparse
import os
import sys
import glob
import re

def natural_sort_key(s):
    """自然排序key函数，将数字部分转为整数比较"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def format_value(val):
    """ADOFAI 格式（小写 true/false，带尾随逗号的类 JSON）"""
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

def generate_video_adofai(frame_paths, output_path, fps=DEFAULT_FPS, zoom=DEFAULT_ZOOM):
    """
    将视频帧序列转换为ADOFAI关卡文件
    
    参数:
    - frame_paths: 帧图片路径列表
    - output_path: 输出.adofai文件路径
    - fps: 帧率
    - zoom: 缩放百分比
    """
    try:
        # 读取所有帧
        print(f"读取 {len(frame_paths)} 帧图片...")
        frames = []
        for i, path in enumerate(frame_paths):
            img = Image.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            frames.append(img)
            print(f"  [{i+1}/{len(frame_paths)}] {os.path.basename(path)}")
        
        # 检查所有帧尺寸是否一致
        width, height = frames[0].size
        for i, frame in enumerate(frames[1:], 1):
            if frame.size != (width, height):
                print(f"错误: 帧 {i+1} 的尺寸 {frame.size} 与第一帧 {(width, height)} 不一致")
                sys.exit(1)
        
        num_frames = len(frames)
        pixels_per_frame = width * height
        
        print(f"\n视频信息:")
        print(f"  帧数: {num_frames}")
        print(f"  分辨率: {width}×{height}")
        print(f"  每帧像素: {pixels_per_frame}")
        print(f"  FPS: {fps}")
        print(f"  BPM: {fps * 60}")
        print(f"  Zoom: {zoom}%")
        
        # 计算BPM（转为整数）
        bpm = int(fps * 60)
        
        # 计算总Floor数
        # Director区: num_frames个Floor
        # Frame区: num_frames × pixels_per_frame个Floor
        # 额外+1: 最后添加一个占位Floor，确保最后一个像素能被渲染
        total_floors = num_frames + (num_frames * pixels_per_frame) + 1
        
        print(f"\n关卡统计:")
        print(f"  Director区: {num_frames} 个Floor")
        print(f"  Frame区: {num_frames * pixels_per_frame} 个Floor")
        print(f"  占位Floor: 1 个")
        print(f"  总Floor数: {total_floors}")
        print(f"  angleData数量: {total_floors - 1}")
        
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
        
        settings = [
            ("version", 15),
            ("artist", ""),
            ("specialArtistType", "None"),
            ("artistPermission", ""),
            ("song", ""),
            ("author", ""),
            ("separateCountdownTime", True),
            ("previewImage", ""),
            ("previewIcon", ""),
            ("previewIconColor", "003f52"),
            ("previewSongStart", 0),
            ("previewSongDuration", 10),
            ("seizureWarning", False),
            ("levelDesc", f"Video {width}×{height} {fps}FPS {num_frames}frames"),
            ("levelTags", "video"),
            ("artistLinks", ""),
            ("speedTrialAim", 0),
            ("difficulty", 1),
            ("requiredMods", []),
            ("songFilename", ""),
            ("bpm", bpm),
            ("volume", 100),
            ("offset", 0),
            ("pitch", 100),
            ("hitsound", "Kick"),
            ("hitsoundVolume", 100),
            ("countdownTicks", 4),
            ("tileShape", "Short"),
            ("trackColorType", "Single"),
            ("trackColor", "000000"),  # 默认黑色
            ("secondaryTrackColor", "ffffff"),
            ("trackColorAnimDuration", 2),
            ("trackColorPulse", "None"),
            ("trackPulseLength", 10),
            ("trackStyle", "Minimal"),
            ("trackTexture", ""),
            ("trackTextureScale", 1),
            ("trackGlowIntensity", 100),
            ("trackAnimation", "None"),
            ("beatsAhead", 3),
            ("trackDisappearAnimation", "None"),
            ("beatsBehind", 4),
            ("backgroundColor", "ffffff"),
            ("showDefaultBGIfNoImage", False),
            ("showDefaultBGTile", False),
            ("defaultBGTileColor", "101121"),
            ("defaultBGShapeType", "Default"),
            ("defaultBGShapeColor", "ffffff"),
            ("bgImage", ""),
            ("bgImageColor", "ffffff"),
            ("parallax", [100, 100]),
            ("bgDisplayMode", "FitToScreen"),
            ("imageSmoothing", True),
            ("lockRot", False),
            ("loopBG", False),
            ("scalingRatio", 100),
            ("relativeTo", "Player"),
            ("position", [0, 0]),
            ("rotation", 0),
            ("zoom", 100),
            ("pulseOnFloor", True),
            ("startCamLowVFX", False),
            ("bgVideo", ""),
            ("loopVideo", False),
            ("vidOffset", 0),
            ("floorIconOutlines", False),
            ("stickToFloors", True),
            ("planetEase", "Linear"),
            ("planetEaseParts", 1),
            ("planetEasePartBehavior", "Mirror"),
            ("customClass", ""),
            ("defaultTextColor", "ffffff"),
            ("defaultTextShadowColor", "00000050"),
            ("congratsText", ""),
            ("perfectText", ""),
            ("legacyFlash", False),
            ("legacyCamRelativeTo", False),
            ("legacySpriteTiles", False),
            ("legacyTween", False),
            ("disableV15Features", False),
        ]
        
        for i, (key, val) in enumerate(settings):
            comma = "," if i < len(settings) - 1 else ""
            lines.append(f'\t\t"{key}": {format_value(val)}{comma}')
        
        lines.append('\t},')
        
        # actions
        lines.append('\t"actions":')
        lines.append('\t[')
        
        actions = []
        
        print("\n生成Director区...")
        # Director区: Floor 1 到 Floor num_frames
        for frame_idx in range(num_frames):
            floor = frame_idx + 1
            
            # 计算该帧的中心全局坐标
            # 第N帧第一个像素的Y坐标 = FRAME_START_Y_OFFSET - frame_idx × (height × FLOOR_HEIGHT + FRAME_GAP)
            frame_y_start = FRAME_START_Y_OFFSET - frame_idx * (height * FLOOR_HEIGHT + FRAME_GAP)
            camera_x = width / 2
            camera_y = frame_y_start - (height * FLOOR_HEIGHT) / 2
            
            # MoveCamera事件
            move_camera = (floor, f'\t\t{{ "floor": {floor}, "eventType": "MoveCamera", "duration": 0, "relativeTo": "Global", "position": [{camera_x}, {camera_y}], "zoom": {zoom}, "angleOffset": 0, "ease": "Linear", "dontDisable": false, "minVfxOnly": false, "eventTag": ""}}')
            actions.append(move_camera)
            
            if (frame_idx + 1) % 10 == 0 or frame_idx == num_frames - 1:
                print(f"  Director Floor {floor}: 帧{frame_idx+1} 中心=({camera_x}, {camera_y})")
        
        print("\n生成Frame区...")
        # Frame区: 从 Floor (num_frames + 1) 开始
        current_floor = num_frames + 1
        
        for frame_idx in range(num_frames):
            pixels = list(frames[frame_idx].getdata())
            
            print(f"  处理帧 {frame_idx+1}/{num_frames}...")
            
            for pixel_idx in range(pixels_per_frame):
                floor = current_floor
                current_floor += 1
                
                # 获取像素颜色
                r, g, b, a = pixels[pixel_idx]
                hex_color = f"{r:02x}{g:02x}{b:02x}{a:02x}"
                
                # ColorTrack事件
                color_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "ColorTrack", "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Minimal", "trackTexture": "", "trackTextureScale": 1, "trackGlowIntensity": 100, "justThisTile": false}}')
                actions.append(color_action)
                
                # PositionTrack逻辑
                # 1. 第一帧第一个像素：从Director跳到Frame区
                if frame_idx == 0 and pixel_idx == 0:
                    # Frame区第一个Floor自然连接到(num_frames+1, 0)
                    # 需要移动到(0, FRAME_START_Y_OFFSET)
                    x_offset = -(num_frames + 1)
                    y_offset = FRAME_START_Y_OFFSET
                    pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                    actions.append(pos_action)
                
                # 2. 非第一帧的第一个像素：从上一帧跳到当前帧
                elif pixel_idx == 0 and frame_idx > 0:
                    x_offset = -width
                    # Y偏移 = 最后一次换行 + 帧间距
                    y_offset = -(ROW_OFFSET + FRAME_GAP)
                    pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                    actions.append(pos_action)
                
                # 3. 帧内换行：每行第一个像素（但不是帧的第一个像素）
                else:
                    # pixel_idx对应实际位置
                    col = pixel_idx % width
                    
                    # 如果是行首（col=0）且不是第一个像素，说明需要换行
                    if col == 0 and pixel_idx > 0:
                        x_offset = -width
                        y_offset = -ROW_OFFSET
                        pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                        actions.append(pos_action)
        
        # 按floor编号排序
        actions.sort(key=lambda x: x[0])
        
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
        print(f"\n写入文件: {output_path}")
        content = "\n".join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✓ 成功生成 ADOFAI 视频关卡!")
        print(f"  输出文件: {output_path}")
        print(f"  总事件数: {len(actions)}")
        
    except FileNotFoundError as e:
        print(f"错误: 找不到文件 '{e.filename}'")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='视频帧序列转 ADOFAI 关卡')
    parser.add_argument('frames', nargs='+', help='帧图片文件路径（支持通配符）')
    parser.add_argument('-o', '--output', required=True, help='输出 .adofai 文件路径')
    parser.add_argument('--fps', type=float, default=DEFAULT_FPS, help=f'帧率（默认 {DEFAULT_FPS}）')
    parser.add_argument('--zoom', type=int, default=DEFAULT_ZOOM, help=f'缩放百分比（默认 {DEFAULT_ZOOM}）')
    
    args = parser.parse_args()
    
    # 处理通配符
    frame_paths = []
    for pattern in args.frames:
        if '*' in pattern or '?' in pattern:
            matched = glob.glob(pattern)
            frame_paths.extend(sorted(matched, key=natural_sort_key))
        else:
            frame_paths.append(pattern)
    
    # 如果没有通配符，也进行自然排序
    frame_paths = sorted(frame_paths, key=natural_sort_key)
    
    if not frame_paths:
        print("错误: 没有找到任何帧图片文件")
        sys.exit(1)
    
    # 验证fps
    if args.fps <= 0:
        print(f"错误: FPS必须大于0，当前值: {args.fps}")
        sys.exit(1)
    
    print(f"找到 {len(frame_paths)} 个帧文件")
    
    generate_video_adofai(frame_paths, args.output, args.fps, args.zoom)
