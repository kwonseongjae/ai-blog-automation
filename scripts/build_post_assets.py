"""글 목록의 표지와 설명 그림을 같은 서체·색상으로 만든다. Pillow가 필요하다."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/posts/assets'
FONT = Path.home() / '.local/share/fonts'
INK, BLUE, MUTED = '#202A35', '#355EC7', '#667385'


def font(size, bold=False):
    path = FONT / ('NanumGothic-Bold.ttf' if bold else 'NanumGothic-Regular.ttf')
    if not path.is_file():
        raise FileNotFoundError('NanumGothic 서체를 사용자 fonts 폴더에 설치하세요')
    return ImageFont.truetype(str(path), size)


def save(image, name, title):
    meta = PngImagePlugin.PngInfo()
    meta.add_text('Author', '권성재')
    meta.add_text('Title', title)
    image.save(OUT / name, pnginfo=meta)
    assert image.width >= 900 and image.height >= 660


def cover(article):
    """목록 썸네일(가로 168px)에서도 읽히도록 큰 글자를 파란 바탕에 꽉 채운다."""
    label, line1, line2, caption = article['cover_text']
    image = Image.new('RGB', (1280, 720), BLUE)
    draw = ImageDraw.Draw(image)
    draw.text((80, 72), label, font=font(46, True), fill='#FFE680', anchor='lt')
    y = 170
    for text, base in [(line1, 156), (line2, 112)]:
        size = base
        while draw.textlength(text, font=font(size, True)) > 1120:
            size -= 1
        draw.text((80, y), text, font=font(size, True), fill='white', anchor='lt')
        y += int(size * 1.3)
    assert draw.textlength(caption, font=font(40)) < 1120, '표지 설명이 너무 깁니다'
    draw.text((80, 520), caption, font=font(40), fill='#DCE5FA', anchor='lt')
    draw.line((80, 620, 1200, 620), fill='#6F8FE0', width=2)
    draw.text((80, 648), 'Jack의 AI 개발노트', font=font(34, True), fill='white', anchor='lt')
    save(image, article['id'] + '-cover.png', line1 + ' ' + line2)


def flow(article):
    image = Image.new('RGB', (900, 660), 'white')
    draw = ImageDraw.Draw(image)
    draw.text((48, 32), article['diagram_title'], font=font(29, True), fill=INK, anchor='lt')
    for index, (title, detail) in enumerate(article['diagram_steps']):
        y = 102 + index * 176
        draw.rounded_rectangle((48, y, 852, y + 136), radius=10, fill='#F5F7FA', outline='#E5E9EF', width=2)
        draw.text((76, y + 32), str(index + 1).zfill(2), font=font(32, True), fill=BLUE, anchor='lt')
        draw.text((154, y + 24), title, font=font(37, True), fill=INK, anchor='lt')
        draw.text((154, y + 82), detail, font=font(27), fill=MUTED, anchor='lt')
        assert draw.textlength(detail, font=font(27)) < 660, '그림 설명이 너무 깁니다'
        if index < 2:
            draw.line((450, y + 143, 450, y + 167), fill=BLUE, width=3)
            draw.polygon([(443, y + 159), (457, y + 159), (450, y + 169)], fill=BLUE)
    save(image, article['id'] + '-flow.png', article['diagram_title'])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalogue = json.loads((ROOT / 'docs/posts/catalogue.json').read_text())
    count = 0
    for article in catalogue:
        if article.get('cover_text'):
            cover(article)
            count += 1
        if article.get('diagram_steps'):
            assert len(article['diagram_steps']) == 3
            flow(article)
            count += 1
    print(f'이미지 {count}개 생성 · 작성자 권성재 · 표지 1280×720 · 흐름 그림 900×660')


if __name__ == '__main__':
    main()
