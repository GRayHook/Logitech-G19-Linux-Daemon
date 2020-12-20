# coding: utf-8
#
""" Helper for drawing"""
import os
import timeit
import PIL.Image as Img
import PIL.ImageDraw as Draw
import PIL.ImageFont as Font
from g19d import libcdraw
import ctypes


class Drawer(object):
    """docstring for Drawer."""
    def __init__(self):
        super(Drawer, self).__init__()
        self.__frame = libcdraw.Frame()

    def get_frame_data(self):
        """Getter for frame data"""
        return self.__frame.get_bytes()

    def draw_rectangle(self, position, size, color_rgb):
        """Draw rectangle on frame"""
        color = libcdraw.rgb_to_uint16(color_rgb[0], color_rgb[1], color_rgb[2])
        if len(color_rgb) > 3:
            alpha = color_rgb[3]
        else:
            alpha = 1.0

        new_frame = self.__frame.draw_rectangle(position[0], position[1], size[0], size[1], color, alpha)

    def draw_image_from_file(self, position, size, filename):
        """Draw image frome file"""
        img = Img.open(filename)
        self.draw_image(position, size, img)

    def draw_image(self, position, size, img):
        """Draw image"""
        if img.size != (size[0], size[1]):
            img = img.resize((size[0], size[1]), Img.CUBIC)

        image = img.convert(mode='BGR;16').tobytes()
        if img.mode == "RGBA":
            mask = img.split()[-1].tobytes()
        else:
            mask = bytes([255] * (size[0] * size[1]))

        new_frame = self.__frame.copy_rectangle(position[0], position[1], size[0], size[1], image, mask)

    def draw_text(self, position, size, img, color=0x00):
        msk = img.tobytes()
        new_frame = self.__frame.copy_text(position[0], position[1], size[0], size[1], color, msk)

    def draw_text_fitted(self, position, font_size, text):
        """Draw text"""
        font = Font.truetype(os.path.dirname(__file__) + "/11676.otf", font_size)
        height = font_size
        maxwidth = 0
        i = 0
        rows = []
        row = ""
        row_len = 0
        for char in text:
            char_len = font.getsize(char)[0]
            overflow = row_len + char_len > 320 - position[0]
            if overflow:
                if char == " " or char == "\n":
                    continue
                if maxwidth < row_len:
                    maxwidth = row_len
            if overflow or char == "\n":
                if height + font_size + 15 > 240 - position[1]:
                    break
                height += font_size + 15
                rows.append(row.rstrip().lstrip("\n"))
                row = char
                row_len = char_len
            if overflow:
                continue
            row_len += char_len
            row += char
        if row and char != " " and char != "\n":
            rows.append(row.rstrip().lstrip("\n"))
            if maxwidth < row_len:
                maxwidth = row_len

        text = "\n".join(rows)
        img = Img.new("L", (maxwidth, height), ("black"))
        draw = Draw.Draw(img)
        draw.text([0, 0], text, ("white"), font=font)
        self.draw_text(position, [maxwidth, height], img)

    def draw_textline(self, position, font_size, text, color=0x00):
        """Draw text"""
        font = Font.truetype(os.path.dirname(__file__) + "/11676.otf", font_size)
        width = 0
        for i in range(len(text)):
            width += font.getsize(text[i])[0]
            if text[i] == '\n' or width > 320 - position[0]:
                text = text[:i-1]
                break
        img = Img.new("L", (320 - position[0], font_size), ("black"))
        draw = Draw.Draw(img)
        draw.text([0, -int(font_size * 0.1875)], text, ("white"), font=font)

        self.draw_text(position, [320 - position[0], font_size], img, color)



if __name__ == '__main__':
    print("( '-')")
