#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADOFAI 工具集 - 统一配置
"""

# ==================== 视频转ADOFAI配置 ====================

# 帧渲染起始位置（相对于Director区）
FRAME_START_Y_OFFSET = -10

# 帧间距离（每帧之间的垂直间距）
FRAME_GAP = 10

# 行间距（帧内每行之间的垂直间距）
ROW_OFFSET = 0.9

# Floor尺寸（游戏引擎固定值，不建议修改）
FLOOR_WIDTH = 1
FLOOR_HEIGHT = 0.9

# 默认参数
DEFAULT_FPS = 5
DEFAULT_ZOOM = 100
DEFAULT_Y_OFFSET = 0.9

# ==================== 图片处理配置 ====================

# 支持的图片格式
SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp']

# 默认JPEG质量
DEFAULT_JPEG_QUALITY = 95

# ==================== ADOFAI Settings 模板 ====================

def get_adofai_settings(level_desc="", level_tags="", bpm=100, zoom=100, 
                        track_color="000000", position=None, relative_to="Player"):
    """
    生成ADOFAI关卡settings配置
    
    参数:
        level_desc: 关卡描述
        level_tags: 关卡标签
        bpm: BPM值
        zoom: 缩放百分比
        track_color: 轨道颜色
        position: 初始位置 [x, y]
        relative_to: 相对位置参考
    
    返回:
        list: settings配置列表
    """
    if position is None:
        position = [0, 0]
    
    return [
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
        ("levelDesc", level_desc),
        ("levelTags", level_tags),
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
        ("trackColor", track_color),
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
        ("relativeTo", relative_to),
        ("position", position),
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
