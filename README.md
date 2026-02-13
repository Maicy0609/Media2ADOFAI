# Media2ADOFAI

将图片或视频转换成 ADOFAI 关卡文件，无需使用任何图片文件。

## 功能特性

- 🖼️ **图片转ADOFAI**: 将单张图片转换为像素艺术关卡
- 🎬 **视频转ADOFAI**: 将视频帧序列转换为动态关卡
  - v1: ColorTrack方案（每帧独立轨道）
  - v2: RecolorTrack方案（共享轨道，更高效）
- 📹 **视频提取帧**: 从视频中提取帧图片
- 📐 **批量缩放**: 批量缩放图片尺寸

## 安装

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
# 必需依赖
pip install Pillow

# 视频提取帧功能需要
pip install opencv-python
```

## 使用方法

### 方式一：交互式菜单

```bash
python main.py
```

### 方式二：命令行

```bash
# 查看帮助
python cli.py --help

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
```

### 方式三：作为模块导入

```python
from core import generate_image_adofai, generate_video_adofai

# 图片转ADOFAI
generate_image_adofai('image.png', 'output.adofai')

# 视频帧转ADOFAI
frames = ['frame1.png', 'frame2.png', ...]
generate_video_adofai(frames, 'output.adofai', fps=5, zoom=100)
```

## 项目结构

```
Media2ADOFAI/
├── config.py           # 统一配置
├── utils.py            # 公共工具函数
├── core/
│   ├── __init__.py
│   ├── frame_extract.py    # 视频提取帧
│   ├── image_resize.py     # 图片缩放
│   ├── image2adofai.py     # 图片转ADOFAI
│   └── video2adofai.py     # 视频转ADOFAI (v1/v2)
├── cli.py              # 命令行入口
├── main.py             # 交互式入口
├── requirements.txt    # 依赖列表
└── README.md
```

## 配置说明

可在 `config.py` 中修改以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| DEFAULT_FPS | 5 | 默认帧率 |
| DEFAULT_ZOOM | 100 | 默认缩放百分比 |
| DEFAULT_Y_OFFSET | 0.9 | 默认行间距 |
| FRAME_GAP | 10 | 帧间距 |
| ROW_OFFSET | 0.9 | 行间距 |

## 版本对比

| 特性 | v1 (ColorTrack) | v2 (RecolorTrack) |
|------|-----------------|-------------------|
| 砖块数 | 帧数×像素数 | 像素数 |
| 事件数 | 较多 | 较少 |
| 适用场景 | 小视频 | 大视频/长视频 |
| 性能 | 一般 | 更高效 |

## 许可证

MIT License
