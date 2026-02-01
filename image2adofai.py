import json
from PIL import Image
import argparse
import os
import sys

def clean_path(path):
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
    return os.path.dirname(os.path.abspath(__file__))

def resolve_output_path(user_output, input_path, script_dir):
    if not user_output:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(script_dir, f"{base_name}.adofai")
    user_output = clean_path(user_output)
    if os.path.isabs(user_output):
        return user_output
    return os.path.join(script_dir, user_output)

def format_value(val):
    """ADOFAI 格式（小写 true/false，带尾随逗号的类 JSON）"""
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, str):
        return f'"{val}"'
    elif isinstance(val, list):
        items = [format_value(v) for v in val]
        return f'[{", ".join(items)}]'
    return str(val)

def generate_adofai(image_path, output_path, y_offset=0.9):
    """
    将单张图片转换为 ADOFAI 像素艺术关卡
    
    参数:
        image_path: 输入图片路径
        output_path: 输出 .adofai 文件路径
        y_offset: Y轴偏移量（正数，控制行间距，默认0.9）
    
    异常:
        失败时抛出异常
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            width, height = img.size
            total_pixels = width * height
            
            if total_pixels < 1:
                raise ValueError("图片不能为空")
            
            print(f"图片尺寸: {width}x{height} = {total_pixels} 个像素")
            print(f"砖块布局: {width}×{height} 矩阵 (共 {total_pixels} 个砖块)")
            
            pixels = list(img.getdata())
            
            first_pixel = pixels[0]
            r, g, b, a = first_pixel
            first_color = f"{r:02x}{g:02x}{b:02x}{a:02x}"
            
            lines = []
            lines.append("{")
            
            link_count = total_pixels - 1
            angles = ", ".join(["0"] * link_count)
            lines.append(f'\t"angleData": [{angles}], ')
            
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
                ("levelDesc", f"PixelArt {width}×{height}"),
                ("levelTags", "pixelart"),
                ("artistLinks", ""),
                ("speedTrialAim", 0),
                ("difficulty", 1),
                ("requiredMods", []),
                ("songFilename", ""),
                ("bpm", 100),
                ("volume", 100),
                ("offset", 0),
                ("pitch", 100),
                ("hitsound", "Kick"),
                ("hitsoundVolume", 100),
                ("countdownTicks", 4),
                ("tileShape", "Short"),
                ("trackColorType", "Single"),
                ("trackColor", first_color),
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
            
            lines.append('\t"actions":')
            lines.append('\t[')
            
            actions = []
            
            for idx in range(1, total_pixels):
                floor = idx
                
                pixel_position = idx - 1
                col = pixel_position % width
                row = pixel_position // width
                
                r, g, b, a = pixels[idx]
                hex_color = f"{r:02x}{g:02x}{b:02x}{a:02x}"
                
                color_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "ColorTrack", "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Minimal", "trackTexture": "", "trackTextureScale": 1, "trackGlowIntensity": 100, "justThisTile": false}}')
                actions.append(color_action)
                
                if col == width - 1:
                    y_value = -y_offset
                    pos_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "PositionTrack", "positionOffset": [{-width}, {y_value}], "relativeTo": [0, "ThisTile"], "justThisTile": false, "editorOnly": false}}')
                    actions.append(pos_action)
            
            actions.sort(key=lambda x: x[0])
            
            for i, (_, action_str) in enumerate(actions):
                if i < len(actions) - 1:
                    lines.append(action_str + ",")
                else:
                    lines.append(action_str)
            
            lines.append('\t],')
            
            lines.append('\t"decorations":')
            lines.append('\t[')
            lines.append('\t]')
            
            lines.append("}")
            
            content = "\n".join(lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ 成功生成 ADOFAI 关卡: {output_path}")
            print(f"  首像素颜色: {first_color} (已写入 settings.trackColor)")
            print(f"  事件数量: {len(actions)} 个")
            print(f"  换行次数: {height - 1} 次")
            
    except FileNotFoundError:
        print(f"错误: 找不到图片文件 '{image_path}'")
        raise
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """命令行入口（使用 argparse）"""
    script_dir = get_script_dir()
    
    parser = argparse.ArgumentParser(description='图片转 ADOFAI 像素艺术')
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-o', '--output', help='输出 .adofai 文件路径（默认使用图片名）')
    parser.add_argument('-y', '--y-offset', type=float, default=0.9, 
                       help='Y轴偏移量（正数，默认0.9）')
    
    args = parser.parse_args()
    
    if args.y_offset <= 0:
        print(f"错误: Y轴偏移量必须大于0，当前值: {args.y_offset}")
        sys.exit(1)
    
    img_path = clean_path(args.image)
    out_path = resolve_output_path(args.output, img_path, script_dir)
    
    try:
        generate_adofai(img_path, out_path, args.y_offset)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
