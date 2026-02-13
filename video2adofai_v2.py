import json
from PIL import Image
import argparse
import os
import sys
import glob
import re

# ==================== CONFIG ====================
ROW_OFFSET = 0.9  # 行间距
DEFAULT_FPS = 5
DEFAULT_ZOOM = 100
# ================================================

def natural_sort_key(s):
    """自然排序key函数"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def format_value(val):
    """ADOFAI 格式"""
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

def generate_video_adofai_v2(frame_paths, output_path, fps=DEFAULT_FPS, zoom=DEFAULT_ZOOM):
    """
    使用RecolorTrack方案生成视频ADOFAI
    
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
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(frame_paths)}]")
        
        # 检查所有帧尺寸是否一致
        width, height = frames[0].size
        for i, frame in enumerate(frames[1:], 1):
            if frame.size != (width, height):
                print(f"错误: 帧 {i+1} 的尺寸 {frame.size} 与第一帧 {(width, height)} 不一致")
                sys.exit(1)
        
        num_frames = len(frames)
        pixels_per_frame = width * height
        position_value = [width / 2, -height / 2]

        # BPM固定为60
        bpm = 60
        
        # 角度间隔公式：d = 3 × BPM / fps
        d = 3 * bpm / fps
        
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
        
        print(f"\n关卡统计:")
        print(f"  砖块数: {total_floors}")
        print(f"  angleData数量: {total_floors}")
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
            ("levelDesc", "Video"),
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
            ("trackColor", "000000"),
            ("secondaryTrackColor", "ffffff"),
            ("trackColorAnimDuration", 2),
            ("trackColorPulse", "None"),
            ("trackPulseLength", 10),
            ("trackStyle", "Basic"),
            ("trackTexture", ""),
            ("trackTextureScale", 1),
            ("trackGlowIntensity", 100),
            ("trackAnimation", "None"),
            ("beatsAhead", 3),
            ("trackDisappearAnimation", "None"),
            ("beatsBehind", 4),
            ("backgroundColor", "000000"),
            ("showDefaultBGIfNoImage", True),
            ("showDefaultBGTile", True),
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
            ("relativeTo", "Global"),
            ("position", position_value),
            ("rotation", 0),
            ("zoom", zoom),
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
        
        print("\n生成RecolorTrack...")
        
        # 使用已计算的d值
        
        # 先收集所有Floor 1的RecolorTrack（不排序，直接按顺序）
        floor1_actions = []
        
        for frame_idx in range(num_frames):
            angle_offset = frame_idx * d
            pixels = list(frames[frame_idx].getdata())
            
            for pixel_idx in range(pixels_per_frame):
                tile_index = pixel_idx + 1
                r, g, b, a = pixels[pixel_idx]
                hex_color = f"{r:02x}{g:02x}{b:02x}{a:02x}"
                
                # 直接拼接字符串，不用元组
                floor1_actions.append(f'\t\t{{ "floor": 1, "eventType": "RecolorTrack", "startTile": [{tile_index}, "Start"], "endTile": [{tile_index}, "Start"], "gapLength": 0, "duration": 0, "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Basic", "trackGlowIntensity": 100, "angleOffset": {angle_offset}, "ease": "Linear", "eventTag": ""}}')
            
            if (frame_idx + 1) % 10 == 0 or frame_idx == num_frames - 1:
                print(f"  帧 {frame_idx + 1}/{num_frames}: {len(floor1_actions)} 个RecolorTrack")
        
        print("\n生成PositionTrack（换行）...")
        
        # 收集其他Floor的PositionTrack
        other_actions = {}  # floor -> action_str
        
        for floor in range(2, total_floors + 1):  # 从Floor 2开始
            pixel_idx = floor - 1
            col = pixel_idx % width
            
            if col == width - 1 and floor < total_floors:
                x_offset = -width
                y_offset = -ROW_OFFSET
                other_actions[floor] = f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{x_offset}, {y_offset}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}'
        
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
        
        print(f"\n✓ 成功生成 ADOFAI 视频关卡!")
        print(f"  输出文件: {output_path}")
        print(f"  砖块数: {total_floors}")
        print(f"  总事件数: {len(floor1_actions) + len(other_actions)}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='视频帧转 ADOFAI (RecolorTrack方案)')
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
    
    if not frame_paths:
        print("错误: 没有找到任何帧图片文件")
        sys.exit(1)
    
    if args.fps <= 0:
        print(f"错误: FPS必须大于0")
        sys.exit(1)
    
    print(f"找到 {len(frame_paths)} 个帧文件")
    
    generate_video_adofai_v2(frame_paths, args.output, args.fps, args.zoom)
