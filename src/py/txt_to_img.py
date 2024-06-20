# Sample code of converting text to image
# Implemented on QQ bot client


def text_to_img(item_name):
    text = item_roll(item_name)
    print(text)
    font = ImageFont.truetype("times.ttf", 18)
    color = (0, 0, 0)
    background = (255, 255, 255)
    lines = text.split("\n")
    text_widths = []
    text_height = 0
    for line in lines:
        text_bbox = font.getbbox(line)
        text_widths.append(text_bbox[2] - text_bbox[0])
        text_height += text_bbox[3] - text_bbox[1]
    line_spacing = 10
    text_height += (len(lines) - 1) * line_spacing
    image = Image.new('RGB', (max(text_widths), text_height), color=background)
    draw = ImageDraw.Draw(image)
    y = 0
    for line in lines:
        text_bbox = font.getbbox(line)
        x = 0
        draw.text((x, y), line, fill=color, font=font)
        y += text_bbox[3] - text_bbox[1] + line_spacing
    new_size = (image.width + line_spacing, image.height + line_spacing)  # add 10 pixels of padding to the width and height
    resized_image = image.resize(new_size)
    resized_image.save("output.png")
