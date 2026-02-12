import os
import sys
import glob
import re

# 导入项目中的功能模块
from image2adofai import generate_adofai, clean_path, resolve_output_path, get_script_dir
from video2adofai import generate_video_adofai, natural_sort_key
from frame_extract import extract_frames
from imgzip import batch_resize

# 默认值
DEFAULT_FPS = 5
DEFAULT_ZOOM = 100
DEFAULT_Y_OFFSET = 0.9

class ProgressBar:
    """空进度条类"""
    def __init__(self, total, desc):
        pass
    
    def update(self, n=1):
        pass
    
    def close(self):
        pass

def get_input(prompt, default=None, required=False):
    """获取用户输入"""
    while True:
        user_input = input(prompt)
        if user_input.strip():
            return user_input.strip()
        elif default is not None:
            return default
        elif required:
            print("该输入不能为空，请重新输入")
        else:
            return ""

def get_float_input(prompt, default=None, min_value=None, max_value=None):
    """获取浮点数输入"""
    while True:
        user_input = input(prompt)
        if user_input.strip():
            try:
                value = float(user_input.strip())
                if min_value is not None and value < min_value:
                    print(f"输入值必须大于等于{min_value}")
                    continue
                if max_value is not None and value > max_value:
                    print(f"输入值必须小于等于{max_value}")
                    continue
                return value
            except ValueError:
                print("请输入有效的数字")
                continue
        elif default is not None:
            return default
        else:
            print("该输入不能为空，请重新输入")

def get_int_input(prompt, default=None, min_value=None, max_value=None):
    """获取整数输入"""
    while True:
        user_input = input(prompt)
        if user_input.strip():
            try:
                value = int(user_input.strip())
                if min_value is not None and value < min_value:
                    print(f"输入值必须大于等于{min_value}")
                    continue
                if max_value is not None and value > max_value:
                    print(f"输入值必须小于等于{max_value}")
                    continue
                return value
            except ValueError:
                print("请输入有效的整数")
                continue
        elif default is not None:
            return default
        else:
            print("该输入不能为空，请重新输入")

def get_yes_no_input(prompt, default=None):
    """获取是/否输入"""
    while True:
        user_input = input(prompt).lower()
        if user_input.strip():
            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                return False
            else:
                print("请输入 'y' 或 'n'")
                continue
        elif default is not None:
            return default
        else:
            print("该输入不能为空，请重新输入")

def handle_image():
    """处理图片转ADOFAI"""
    print("\n图片转ADOFAI")
    print("=" * 50)
    
    # 获取输入图片路径
    input_path = get_input("请输入图片路径: ", required=True)
    
    # 获取输出路径
    output_path = get_input("请输入输出 .adofai 文件路径（默认使用图片名）: ")
    
    # 获取Y轴偏移量
    y_offset = get_float_input(f"请输入Y轴偏移量（不建议调整，默认{DEFAULT_Y_OFFSET}）: ", 
                              default=DEFAULT_Y_OFFSET, min_value=0.1)
    
    print("\n处理中...")
    
    script_dir = get_script_dir()
    img_path = clean_path(input_path)
    out_path = resolve_output_path(output_path, img_path, script_dir)
    
    pbar = ProgressBar(total=1, desc="生成ADOFAI")
    try:
        generate_adofai(img_path, out_path, y_offset)
        pbar.update(1)
        print(f"\n成功生成: {out_path}")
    except Exception as e:
        print(f"\n错误: {e}")
        return False
    finally:
        pbar.close()
    return True

def handle_video():
    """处理视频帧转ADOFAI"""
    print("\n视频帧转ADOFAI")
    print("=" * 50)
    
    # 获取帧图片路径
    frame_pattern = get_input("请输入帧图片路径（支持通配符，如 frames/*.png）: ", required=True)
    
    # 处理通配符
    frame_paths = []
    if '*' in frame_pattern or '?' in frame_pattern:
        matched = glob.glob(frame_pattern)
        frame_paths.extend(sorted(matched, key=natural_sort_key))
    else:
        frame_paths.append(frame_pattern)
    
    # 如果没有通配符，也进行自然排序
    frame_paths = sorted(frame_paths, key=natural_sort_key)
    
    if not frame_paths:
        print("❌ 错误: 没有找到任何帧图片文件")
        return False
    
    print(f"  找到 {len(frame_paths)} 帧图片")
    
    # 获取输出路径
    output_path = get_input("请输入输出 .adofai 文件路径: ", required=True)
    
    # 获取FPS
    fps = get_float_input(f"请输入帧率（默认 {DEFAULT_FPS}）: ", 
                         default=DEFAULT_FPS, min_value=0.1)
    
    # 获取缩放百分比
    zoom = get_int_input(f"请输入缩放百分比（默认 {DEFAULT_ZOOM}）: ", 
                        default=DEFAULT_ZOOM, min_value=1, max_value=500)
    
    print("\n处理中...")
    
    pbar = ProgressBar(total=1, desc="生成ADOFAI")
    try:
        generate_video_adofai(frame_paths, output_path, fps, zoom)
        pbar.update(1)
        print(f"\n成功生成: {output_path}")
    except Exception as e:
        print(f"\n错误: {e}")
        return False
    finally:
        pbar.close()
    return True

def handle_extract():
    """处理视频帧提取"""
    print("\n视频帧提取")
    print("=" * 50)
    
    # 获取视频路径
    video_path = get_input("请输入视频文件路径: ", required=True)
    
    # 获取输出目录
    output_dir = get_input("请输入输出目录（默认使用视频名创建目录）: ")
    
    # 获取图片格式
    image_format = get_input("请输入图片格式（png/jpg/jpeg/bmp，默认png）: ", 
                           default="png").lower()
    if image_format not in ['png', 'jpg', 'jpeg', 'bmp']:
        image_format = 'png'
    
    # 获取分组大小
    group_size = get_int_input("请输入每组帧数（默认1000）: ", 
                              default=1000, min_value=1)
    
    print("\n处理中...")
    
    pbar = ProgressBar(total=1, desc="提取帧")
    try:
        success = extract_frames(video_path, output_dir, image_format, group_size)
        pbar.update(1)
        if success:
            print("\n提取完成!")
        else:
            print("\n提取失败!")
            return False
    except Exception as e:
        print(f"\n错误: {e}")
        return False
    finally:
        pbar.close()
    return True

def handle_resize():
    """处理图片缩放"""
    print("\n图片缩放")
    print("=" * 50)
    
    # 获取输入文件夹
    input_folder = get_input("请输入输入文件夹路径: ", required=True)
    
    # 获取输出文件夹
    output_folder = get_input("请输入输出文件夹路径: ", required=True)
    
    # 获取缩放模式
    print("\n请选择缩放模式:")
    print("1. 宽度固定（高度等比例）")
    print("2. 高度固定（宽度等比例）")
    print("3. 固定尺寸（可能变形）")
    print("4. 百分比缩放")
    
    mode_choice = get_int_input("请输入模式编号（1-4）: ", 
                              min_value=1, max_value=4)
    
    # 根据模式获取参数
    if mode_choice == 1:
        mode = 'width'
        width = get_int_input("请输入目标宽度: ", min_value=1)
        height = 0
        percent = 0
    elif mode_choice == 2:
        mode = 'height'
        width = 0
        height = get_int_input("请输入目标高度: ", min_value=1)
        percent = 0
    elif mode_choice == 3:
        mode = 'fixed'
        width = get_int_input("请输入目标宽度: ", min_value=1)
        height = get_int_input("请输入目标高度: ", min_value=1)
        percent = 0
    elif mode_choice == 4:
        mode = 'percent'
        width = 0
        height = 0
        percent = get_float_input("请输入缩放百分比: ", 
                                 min_value=1, max_value=1000)
    
    # 获取分组模式
    group_mode = get_yes_no_input("是否使用分组模式（处理part1/part2子文件夹）? (y/n，默认y): ", 
                                default=True)
    
    print("\n处理中...")
    
    pbar = ProgressBar(total=1, desc="缩放图片")
    try:
        result = batch_resize(
            input_folder=input_folder,
            output_folder=output_folder,
            mode=mode,
            width=width,
            height=height,
            percent=percent,
            group_mode=group_mode,
            verbose=True
        )
        pbar.update(1)
        if result['fail'] > 0:
            print(f"\n有 {result['fail']} 张图片处理失败!")
            return False
        else:
            print(f"\n成功处理 {result['success']} 张图片!")
            print(f"  输出位置: {result['output_path']}")
    except Exception as e:
        print(f"\n错误: {e}")
        return False
    finally:
        pbar.close()
    return True

def main():
    """主函数"""
    while True:
        print("\nMedia2ADOFAI 工具集")
        print("=" * 50)
        print("1. 图片转ADOFAI")
        print("2. 视频帧转ADOFAI")
        print("3. 视频提取帧")
        print("4. 图片缩放")
        print("5. 退出")
        print("=" * 50)
        
        # 获取用户选择
        choice = get_int_input("请输入功能编号（1-5）: ", 
                             min_value=1, max_value=5)
        
        # 执行对应功能
        success = False
        if choice == 1:
            success = handle_image()
        elif choice == 2:
            success = handle_video()
        elif choice == 3:
            success = handle_extract()
        elif choice == 4:
            success = handle_resize()
        elif choice == 5:
            print("\n再见！")
            break
        
        # 询问是否继续
        if not get_yes_no_input("\n是否继续使用其他功能? (y/n): ", default=True):
            print("\n再见！")
            break

if __name__ == "__main__":
    main()
