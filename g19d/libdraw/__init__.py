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

class Frame(object):
    """docstring for Frame."""

    def __init__(self):
        super(Frame, self).__init__()
        self.__size_x = 320
        self.__size_y = 240
        self.__pixel_width = 2
        self.__map = bytes([0] * (self.__size_x * self.__size_y * self.__pixel_width))

    def __get_column(self, column_i):
        """Get start point for column by column index"""
        return column_i * self.__size_y * self.__pixel_width

    def get_map(self):
        """Getter for map"""
        return self.__map

    def set_map(self, data):
        """Setter for map"""
        self.__map = data

    @staticmethod
    def rgb_to_uint16(color_rgb):
        """Converts a RGB value to 16bit highcolor (5-6-5).

        @return 16bit highcolor value in little-endian.

        """
        return libcdraw.rgb_to_uint16(color_rgb[0], color_rgb[1], color_rgb[2])

class Drawer(object):
    """docstring for Drawer."""
    def __init__(self, frame):
        super(Drawer, self).__init__()
        self.__frame = frame

    def get_frame_data(self):
        """Getter for frame data"""
        return self.__frame.get_map()

    def set_frame_data(self, data):
        """Setter for frame data"""
        self.__frame.set_map(data)

    def draw_rectangle(self, position, size, color_rgb):
        """Draw rectangle on frame"""
        color = Frame.rgb_to_uint16(color_rgb[:3])
        if len(color_rgb) > 3:
            alpha = color_rgb[3]
        else:
            alpha = 1.0

        buf = self.get_frame_data()
        new_frame = libcdraw.draw_rectangle(buf, position[0], position[1], size[0], size[1], color, alpha)
        self.set_frame_data(new_frame)

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

        buf = self.get_frame_data()
        new_frame = libcdraw.copy_rectangle(buf, position[0], position[1], size[0], size[1], image, mask)
        self.set_frame_data(new_frame)

    def draw_text(self, position, size, img):
        buf = self.get_frame_data()
        msk = img.tobytes()
        new_frame = libcdraw.copy_text(buf, position[0], position[1], size[0], size[1], 0x00, msk)
        self.set_frame_data(new_frame)

    def draw_text_fitted(self, position, font_size, text):
        """Draw text"""
        font = Font.truetype(os.path.dirname(__file__) + "/11676.otf", font_size)
        height = font_size
        width = 0
        maxwidth = 0
        i = 0
        while i < len(text):
            width += font.getsize(text[i])[0]
            if text[i] == '\n':
                if maxwidth < width:
                    maxwidth = width
                width = 0
                height += font_size + 15
            if width > 320 - position[0]:
                if text[i-1] == ' ':
                    text = text[:i-1] + '\n' + text[i:]
                else:
                    text = text[:i-1] + '\n' + text[i-1:]
                if maxwidth < width:
                    maxwidth = width
                width = 0
                height += font_size + 25
            if height > 240 - position[1]:
                text = text[:i-1]
                break
            i += 1
        if maxwidth < width:
            maxwidth = width
        img = Img.new("L", (maxwidth, height), ("black"))
        draw = Draw.Draw(img)
        draw.text([0, 0], text, ("white"), font=font)
        self.draw_text(position, [maxwidth, height], img)

    def draw_textline(self, position, font_size, text):
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
        draw.text([0, 0], text, ("white"), font=font)

        self.draw_text(position, [320 - position[0], font_size], img)



if __name__ == '__main__':
    print("( '-')")
