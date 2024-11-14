"""
Author: RawFish
Description: Handles rendering of item images and visual components
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from datetime import datetime
from .constants import VERSION, STAT_MAPPING, TIER_COLORS, TIER_TRANSLATIONS

class ItemRenderer:
    def __init__(self, font_path):
        self.font_path = font_path
        
    def _get_rate_color(self, rate):
        if rate <= 50:
            return (255, int(165 * (rate / 50)), 0)
        elif rate <= 65:
            return (255, 165, int(90 * ((rate - 50) / 25)))
        elif rate <= 80:
            return (int(255 * ((80 - rate) / 5)), 255, 0)
        elif rate <= 90:
            return (int(255 * ((90 - rate) / 15)), 255, 0)
        else:
            return (0, 255, int(255 * ((rate - 90) / 10)))

    def _draw_text(self, draw, text, position, font, color, anchor="la"):
        draw.text(position, text, font=font, fill=color, anchor=anchor)

    async def render_item_image(self, data, sales, output_path):
        if not data:
            print("No data to render")
            return
        scale_factor = 4
        base_height = 250 * scale_factor
        additional_height = 25 * scale_factor * (
            len(data[list(data.keys())[0]].keys()) + 
            len(data.get('weights', {}).keys()) * 2
        )
        height = base_height + additional_height
        width = 300 * scale_factor
        image = Image.new('RGB', (width, height), (60, 60, 60))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font_path, 10 * scale_factor)
        small_font = ImageFont.truetype(self.font_path, 8 * scale_factor)
        item_name = list(data.keys())[0]
        # Detailed code in nori-bot v1.2.5+, pulling for Marketplace item rendering
        
        # Save final image
        file_name = f"item_sales_{sales['user']}.png"
        output_file = f"{output_path}/{file_name}"
        image.save(output_file)
        return file_name