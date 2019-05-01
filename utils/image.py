import textwrap
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from wand.image import Image as WandImage
from jishaku.functools import executor_function


@executor_function
def circle_func(avatar_bytes, colour):
    with Image.open(avatar_bytes) as img:
        with Image.new("RGBA", img.size, colour) as background:
            with Image.new("L", img.size, 0) as mask:
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([(0, 0), img.size], fill=255)
                background.paste(img, (0, 0), mask=mask)

            final_buffer = BytesIO()

            background.save(final_buffer, "png")

    final_buffer.seek(0)

    return final_buffer


@executor_function
def draw_text_on_img(text, width, image, font, coordinates, font_size=40, text_color=(0, 0, 0)):
    text = textwrap.wrap(text, width=width)
    ret = BytesIO()

    with Image.open(image) as img:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font, font_size)

        x = coordinates[0]
        y = coordinates[1]
        for t in text:
            width, height = font.getsize(t)
            draw.text((x, y), t, font=font, fill=text_color)
            y += height

        img.save(ret, "png")

    ret.seek(0)

    return ret


@executor_function
def gayify_func(user_avatar, alpha):
    ret = BytesIO()

    with Image.open(user_avatar) as background:
        background = background.resize((926, 926)).convert("RGBA")

        with Image.open("assets/images/gay.png") as flag:
            flag.putalpha(alpha)

            gay = Image.alpha_composite(background, flag)

            gay.save(ret, "png")

    ret.seek(0)

    return ret


@executor_function
def merge(img, img2):
    with Image.open(img) as img:
        img = img.convert("RGBA")
        with Image.open(img2) as img2:
            img2 = img2.convert("RGBA")
            ret = BytesIO()
            img.alpha_composite(img2.resize((83, 83)), dest=(31, 33))
            img.save(ret, "png")

    ret.seek(0)

    return ret


@executor_function
def enhance(image, type_, amount, quality=1, fmt="JPEG"):
    with Image.open(image) as img:
        img = img.convert("RGB")
        enhance_type = getattr(ImageEnhance, type_.capitalize(), ImageEnhance.Color)
        enhanced = enhance_type(img).enhance(amount)

        ret = BytesIO()
        enhanced.save(ret, fmt, quality=quality)

    ret.seek(0)
    return ret


@executor_function
def magik(image):
    with WandImage(file=image) as img:
        ret = BytesIO()
        img.liquid_rescale(
            width=int(img.width * 0.4),
            height=int(img.height * 0.4),
            delta_x=1,
            rigidity=0
        )
        img.liquid_rescale(
            width=int(img.width * 1.6),
            height=int(img.height * 1.6),
            delta_x=2,
            rigidity=0
        )

        img.save(file=ret)

    ret.seek(0)
    return ret


@executor_function
def gmagik(image):
    fin = WandImage()
    ret = BytesIO()

    with WandImage(file=image) as gif:
        for f in gif.sequence:
            with WandImage(image=f) as frame:
                frame.transform(resize='800x800>')
                frame.liquid_rescale(width=int(frame.width * 0.5), height=int(frame.height * 0.5), delta_x=1,
                                     rigidity=0)
                frame.liquid_rescale(width=int(frame.width * 1.5), height=int(frame.height * 1.5), delta_x=2,
                                     rigidity=0)
                frame.resize(frame.width, frame.height)
                fin.sequence.append(frame)

    fin.save(file=ret)
    fin.destroy()
    ret.seek(0)
    return ret


async def get_avatar(user):
    ret = BytesIO()
    await user.avatar_url_as(format="png", size=1024).save(ret)

    return ret
