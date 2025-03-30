#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成应用图标
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    # 创建不同尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    # 创建基本图标
    for size in sizes:
        # 创建一个正方形图像，使用RGBA模式支持透明度
        img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制圆形背景
        circle_color = (52, 152, 219)  # 蓝色
        draw.ellipse([(0, 0), (size, size)], fill=circle_color)
        
        # 在中心绘制文字 'D'
        font_size = int(size * 0.6)
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("Arial Bold", font_size)
        except IOError:
            # 如果无法加载特定字体，使用默认字体
            font = ImageFont.load_default()
        
        text = "D"
        text_color = (255, 255, 255)  # 白色
        
        # 计算文本位置以使其居中
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
        position = ((size - text_width) // 2, (size - text_height) // 2 - int(size * 0.05))
        
        # 绘制文字
        draw.text(position, text, font=font, fill=text_color)
        
        # 保存为PNG
        if not os.path.exists('icons'):
            os.makedirs('icons')
        img.save(f'icons/icon_{size}.png')
    
    # 创建.ico文件（用于Windows）
    icons = []
    for size in sizes:
        icon_path = f'icons/icon_{size}.png'
        if os.path.exists(icon_path):
            icons.append(Image.open(icon_path))
    
    if icons:
        # 确保图标按尺寸排序（从小到大）
        icons.sort(key=lambda x: x.size[0])
        icons[0].save('icons/icon.ico', format='ICO', sizes=[(icon.width, icon.height) for icon in icons])
        print("创建了Windows图标: icons/icon.ico")
    
    # 创建.icns文件（用于macOS）
    try:
        # 在macOS上，我们可以使用iconutil命令，但需要先创建特定结构的文件夹
        if os.path.exists('icons/icon.iconset'):
            os.system('rm -rf icons/icon.iconset')
        os.makedirs('icons/icon.iconset', exist_ok=True)
        
        # 准备iconset文件夹结构
        name_map = {
            16: 'icon_16x16.png',
            32: 'icon_16x16@2x.png',  # 也可以是 icon_32x32.png
            64: 'icon_32x32@2x.png',
            128: 'icon_128x128.png',
            256: 'icon_128x128@2x.png',  # 也可以是 icon_256x256.png
            512: 'icon_256x256@2x.png',  # 也可以是 icon_512x512.png
        }
        
        for size in sizes:
            icon_path = f'icons/icon_{size}.png'
            if os.path.exists(icon_path) and size in name_map:
                output_path = f'icons/icon.iconset/{name_map[size]}'
                # 复制文件
                img = Image.open(icon_path)
                img.save(output_path)
        
        # 使用iconutil创建.icns文件
        os.system('iconutil -c icns icons/icon.iconset')
        print("创建了macOS图标: icons/icon.icns")
    except Exception as e:
        print(f"创建macOS图标时出错: {e}")
        print("请确保您的系统支持iconutil命令")

if __name__ == "__main__":
    create_icon()
    print("图标生成完成") 