from PIL import Image, ImageChops
import os

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    return im

def process_brand():
    path = 'assets/logo.jpg' # 实际上是作为素材的图
    if os.path.exists(path):
        img = Image.open(path)
        # 裁剪边缘
        img = trim(img)
        # 保存为覆盖图
        img.save('assets/logo.jpg', 'JPEG', quality=95)
        # 生成图标
        img.save('assets/icon.ico', format='ICO', sizes=[(256, 256)])
        print("Brand processing complete.")

if __name__ == "__main__":
    process_brand()
