from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
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

# テーマ別 OpenAI 加工プロンプト
THEME_PROMPTS = {
    "思考・マインドセット": (
        "This is a watercolor illustration of a cute corgi. "
        "Add a soft, dreamy atmosphere with gentle pastel tones and subtle floating book or star elements in the background. "
        "Keep the corgi character exactly as-is, only enhance the background mood. Watercolor illustration style."
    ),
    "習慣・行動": (
        "This is a watercolor illustration of a cute corgi. "
        "Add a bright, energetic atmosphere with warm sunrise colors and dynamic energy in the background. "
        "Keep the corgi character exactly as-is, only enhance the background mood. Watercolor illustration style."
    ),
    "経営者のメンタル": (
        "This is a watercolor illustration of a cute corgi. "
        "Add a confident, professional atmosphere with cool blue and gold accent tones in the background. "
        "Keep the corgi character exactly as-is, only enhance the background mood. Watercolor illustration style."
    ),
    "お金・事業の考え方": (
        "This is a watercolor illustration of a cute corgi. "
        "Add a sophisticated atmosphere with subtle golden tones and clean business-like background elements. "
        "Keep the corgi character exactly as-is, only enhance the background mood. Watercolor illustration style."
    ),
    "人間関係・コミュニケーション": (
        "This is a watercolor illustration of a cute corgi. "
        "Add a warm, friendly atmosphere with soft pink and orange tones and gentle heart or sparkle elements in the background. "
        "Keep the corgi character exactly as-is, only enhance the background mood. Watercolor illustration style."
    ),
}
DEFAULT_PROMPT = (
    "This is a watercolor illustration of a cute corgi. "
    "Enhance the background with a pleasant, positive atmosphere. "
    "Keep the corgi character exactly as-is. Watercolor illustration style."
)


def edit_with_openai(image_path: str, theme: str, api_key: str) -> bytes:
    """gpt-image-1でテーマに合わせて画像を加工し、PNG bytesを返す"""
    from openai import OpenAI

    # 正方形にクロップしてリサイズ
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    size = min(w, h)
    left = (w - size) // 2
    top = (h - size) // 2
    img = img.crop((left, top, left + size, top + size))
    img = img.resize((1024, 1024), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    client = OpenAI(api_key=api_key)
    prompt = THEME_PROMPTS.get(theme, DEFAULT_PROMPT)

    response = client.images.edit(
        model="gpt-image-1",
        image=("corgi.png", buf, "image/png"),
        prompt=prompt,
        size="1024x1024",
    )

    import base64
    return base64.b64decode(response.data[0].b64_json)


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


def add_speech_bubble(image_path: str, text: str, theme: str = "", output_path: str = None) -> str:
    if output_path is None:
        output_path = image_path

    display_text = _extract_first_line(text)

    img = Image.open(image_path).convert("RGBA")
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
