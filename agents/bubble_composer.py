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

# テーマ別 画像生成プロンプト（generate用）
_GEN_BASE = (
    "Cute watercolor sticker illustration of a corgi puppy. "
    "White irregular wavy sticker border around the character. "
    "Soft cool sage green and mint watercolor splatter background. "
    "Orange-golden and pure white fluffy fur. Big bright green eyes. Black tiny nose. "
    "Chibi cute cartoon style. No yellow tones, no warm tones. "
    "Cool fresh color palette. Clean isolated sticker on white background. "
)

THEME_GEN_PROMPTS = {
    "朝の名言": (
        _GEN_BASE
        + "The corgi is jumping with joy, ears flying up, front paws raised, big happy smile. "
        "Energetic and bright morning energy."
    ),
    "引き寄せ": (
        _GEN_BASE
        + "The corgi is sitting and looking up dreamily at tiny stars and sparkles above. "
        "Soft magical expression, eyes slightly closed, gentle smile."
    ),
    "自己肯定感": (
        _GEN_BASE
        + "The corgi is sitting proudly with chest puffed out, bright confident smile, tail wagging. "
        "Self-assured and happy pose."
    ),
    "メンタル強化": (
        _GEN_BASE
        + "The corgi has a determined and focused expression, sitting tall, tiny fists raised. "
        "Strong and resilient cute pose."
    ),
    "習慣づくり": (
        _GEN_BASE
        + "The corgi is curled up sleeping peacefully, eyes closed with a tiny smile, "
        "fluffy tail wrapped around, small ZZZ bubbles floating above. Cozy and adorable."
    ),
}
_GEN_DEFAULT = _GEN_BASE + "The corgi is sitting and smiling cheerfully, looking straight ahead. Friendly and cute."

# テーマ別 OpenAI 加工プロンプト（edit用・現在未使用）
_CORGI_BASE = (
    "This is a watercolor illustration of a cute corgi. "
    "Keep the corgi character exactly as-is — preserve the white fur as pure white and the golden-brown fur in its natural color. "
    "Do NOT add any yellow, orange, or warm tints to the corgi. Only modify the background. "
    "Watercolor illustration style. "
)
THEME_PROMPTS = {
    "思考・マインドセット": (
        _CORGI_BASE
        + "Add a soft, dreamy background with cool pastel blues and lavenders, subtle floating stars or book elements."
    ),
    "習慣・行動": (
        _CORGI_BASE
        + "Add a bright, energetic background with clear sky blue and fresh green tones, conveying a crisp morning feel."
    ),
    "経営者のメンタル": (
        _CORGI_BASE
        + "Add a confident, professional background with deep cool blue and silver accent tones."
    ),
    "お金・事業の考え方": (
        _CORGI_BASE
        + "Add a clean, sophisticated background with neutral gray and soft teal tones, business-like atmosphere."
    ),
    "人間関係・コミュニケーション": (
        _CORGI_BASE
        + "Add a friendly background with soft cool pink and light purple tones and gentle sparkle elements."
    ),
}
DEFAULT_PROMPT = (
    _CORGI_BASE
    + "Enhance the background with a pleasant, positive atmosphere using cool, balanced tones."
)


def generate_with_openai(theme: str, api_key: str) -> bytes:
    """gpt-image-1でテーマに合ったコーギー画像を生成してPNG bytesを返す"""
    from openai import OpenAI
    import base64

    client = OpenAI(api_key=api_key)
    prompt = THEME_GEN_PROMPTS.get(theme, _GEN_DEFAULT)

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return base64.b64decode(response.data[0].b64_json)


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
    raw = base64.b64decode(response.data[0].b64_json)

    # 黄みを軽減：赤チャンネルを少し下げ、青チャンネルを少し上げる
    corrected = Image.open(io.BytesIO(raw)).convert("RGB")
    r, g, b = corrected.split()
    r = r.point(lambda x: int(x * 0.94))
    g = g.point(lambda x: int(x * 0.98))
    b = b.point(lambda x: min(255, int(x * 1.04)))
    corrected = Image.merge("RGB", (r, g, b))
    out = io.BytesIO()
    corrected.save(out, format="PNG")
    return out.getvalue()


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


THEME_IMAGE_MAP = {
    "朝の名言":   "corgi_morning.png",
    "引き寄せ":   "corgi_dream.png",
    "自己肯定感": "corgi_happy.png",
    "メンタル強化": "corgi_strong.png",
    "習慣づくり": "corgi_sleep.png",
}


def select_image(images_dir: str, theme: str = "") -> str:
    if not os.path.isdir(images_dir):
        return None

    # テーマ対応画像を優先
    theme_file = THEME_IMAGE_MAP.get(theme)
    if theme_file:
        themed_path = os.path.join(images_dir, theme_file)
        if os.path.exists(themed_path):
            return themed_path

    # フォールバック: corgi_main.png → ランダム
    main_path = os.path.join(images_dir, "corgi_main.png")
    if os.path.exists(main_path):
        return main_path

    images = [
        os.path.join(images_dir, f)
        for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    return random.choice(images) if images else None
