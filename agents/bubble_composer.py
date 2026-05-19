from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os
import random

# フォントパス（Ubuntu → Windows の順で探す）
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    r"C:\Windows\Fonts\BIZ-UDGothicB.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\yugothb.ttc",
]

FONT_SIZE = 48
TEXT_COLOR = (255, 255, 255, 255)
SHADOW_COLOR = (20, 10, 5, 220)
OVERLAY_COLOR = (0, 0, 0, 120)
OVERLAY_HEIGHT_RATIO = 0.20
MAX_CHARS = 20

# テーマ→カラーフィルター設定
THEME_FILTERS = {
    "思考・マインドセット": {"brightness": 1.0, "contrast": 1.1, "warmth": 1.05},
    "習慣・行動":           {"brightness": 1.1, "contrast": 1.0, "warmth": 1.1},
    "経営者のメンタル":     {"brightness": 0.95, "contrast": 1.1, "warmth": 0.95},
    "お金・事業の考え方":   {"brightness": 1.05, "contrast": 1.05, "warmth": 1.0},
    "人間関係・コミュニケーション": {"brightness": 1.1, "contrast": 1.0, "warmth": 1.1},
}
DEFAULT_FILTER = {"brightness": 1.0, "contrast": 1.0, "warmth": 1.0}


def _find_font(size=FONT_SIZE):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _extract_first_line(text: str) -> str:
    lines = [l for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
    if not lines:
        return ""
    first = lines[0].strip()
    for sep in ["。", "！", "!", "？", "?"]:
        if sep in first:
            first = first.split(sep)[0] + sep
            break
    if len(first) > MAX_CHARS:
        first = first[:MAX_CHARS - 1] + "…"
    return first


def _apply_theme_filter(img: Image.Image, theme: str) -> Image.Image:
    cfg = THEME_FILTERS.get(theme, DEFAULT_FILTER)

    img = ImageEnhance.Brightness(img).enhance(cfg["brightness"])
    img = ImageEnhance.Contrast(img).enhance(cfg["contrast"])

    # 暖色/寒色フィルター
    warmth = cfg["warmth"]
    if warmth != 1.0:
        r, g, b = img.split()
        if warmth > 1.0:
            factor = warmth - 1.0
            r = ImageEnhance.Brightness(r).enhance(1 + factor * 0.15)
            b = ImageEnhance.Brightness(b).enhance(1 - factor * 0.10)
        else:
            factor = 1.0 - warmth
            b = ImageEnhance.Brightness(b).enhance(1 + factor * 0.15)
            r = ImageEnhance.Brightness(r).enhance(1 - factor * 0.10)
        img = Image.merge("RGB", (r, g, b))

    return img


def add_speech_bubble(image_path: str, text: str, theme: str = "", output_path: str = None) -> str:
    if output_path is None:
        output_path = image_path

    display_text = _extract_first_line(text)

    img = Image.open(image_path).convert("RGB")
    img = _apply_theme_filter(img, theme)
    img = img.convert("RGBA")
    W, H = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if display_text:
        bar_h = int(H * OVERLAY_HEIGHT_RATIO)
        bar_y = H - bar_h
        draw.rectangle([0, bar_y, W, H], fill=OVERLAY_COLOR)

        font_size = FONT_SIZE
        max_text_w = W - 60
        font = _find_font(font_size)
        while font_size > 20:
            font = _find_font(font_size)
            bbox = draw.textbbox((0, 0), display_text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if tw <= max_text_w:
                break
            font_size -= 2

        bbox = draw.textbbox((0, 0), display_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (W - tw) // 2
        ty = bar_y + (bar_h - th) // 2 - 4

        for dx, dy in [(-2, 2), (2, 2), (0, 3)]:
            draw.text((tx + dx, ty + dy), display_text, font=font, fill=SHADOW_COLOR)
        draw.text((tx, ty), display_text, font=font, fill=TEXT_COLOR)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(output_path, "PNG")
    return output_path


def select_image(images_dir: str, theme: str = "") -> str:
    if not os.path.isdir(images_dir):
        return None
    images = [
        os.path.join(images_dir, f)
        for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not images:
        return None
    return random.choice(images)
