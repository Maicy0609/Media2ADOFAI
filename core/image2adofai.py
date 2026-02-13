#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片转ADOFAI像素艺术模块
"""

import os
import sys

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import format_value, clean_path, resolve_output_path, get_script_dir, pixel_to_hex
from config import get_adofai_settings, DEFAULT_Y_OFFSET


def generate_image_adofai(image_path, output_path, y_offset=None):
    """
    将单张图片转换为 ADOFAI 像素艺术关卡
    
    参数:
        image_path: 输入图片路径
        output_path: 输出 .adofai 文件路径
        y_offset: Y轴偏移量（正数，控制行间距，默认从config读取）
    
    返回:
        bool: 是否成功
    
    异常:
        失败时抛出异常
    """
    if not PIL_AVAILABLE:
        raise ImportError("需要安装 Pillow: pip install Pillow")
    
    if y_offset is None:
        y_offset = DEFAULT_Y_OFFSET
    
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
            first_color = pixel_to_hex(*first_pixel)
            
            lines = []
            lines.append("{")
            
            # angleData
            link_count = total_pixels - 1
            angles = ", ".join(["0"] * link_count)
            lines.append(f'\t"angleData": [{angles}], ')
            
            # settings
            lines.append('\t"settings":')
            lines.append('\t{')
            
            settings = get_adofai_settings(
                level_desc=f"PixelArt {width}×{height}",
                level_tags="pixelart",
                track_color=first_color
            )
            
            for i, (key, val) in enumerate(settings):
                comma = "," if i < len(settings) - 1 else ""
                lines.append(f'\t\t"{key}": {format_value(val)}{comma}')
            
            lines.append('\t},')
            
            # actions
            lines.append('\t"actions":')
            lines.append('\t[')
            
            actions = []
            
            for idx in range(1, total_pixels):
                floor = idx
                
                pixel_position = idx - 1
                col = pixel_position % width
                row = pixel_position // width
                
                hex_color = pixel_to_hex(*pixels[idx])
                
                # ColorTrack事件
                color_action = (floor, f'\t\t{{ "floor": {floor}, "eventType": "ColorTrack", "trackColorType": "Single", "trackColor": "{hex_color}", "secondaryTrackColor": "ffffff", "trackColorAnimDuration": 2, "trackColorPulse": "None", "trackPulseLength": 10, "trackStyle": "Minimal", "trackTexture": "", "trackTextureScale": 1, "trackGlowIntensity": 100, "justThisTile": false}}')
                actions.append(color_action)
                
                # 换行PositionTrack
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
            
            # decorations
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
            
            return True
            
    except FileNotFoundError:
        print(f"错误: 找不到图片文件 '{image_path}'")
        raise
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """命令行入口"""
    import argparse
    
    script_dir = get_script_dir()
    
    parser = argparse.ArgumentParser(description='图片转 ADOFAI 像素艺术')
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-o', '--output', help='输出 .adofai 文件路径（默认使用图片名）')
    parser.add_argument('-y', '--y-offset', type=float, default=DEFAULT_Y_OFFSET, 
                       help=f'Y轴偏移量（正数，默认{DEFAULT_Y_OFFSET}）')
    
    args = parser.parse_args()
    
    if args.y_offset <= 0:
        print(f"错误: Y轴偏移量必须大于0，当前值: {args.y_offset}")
        sys.exit(1)
    
    img_path = clean_path(args.image)
    out_path = resolve_output_path(args.output, img_path, script_dir)
    
    try:
        generate_image_adofai(img_path, out_path, args.y_offset)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
