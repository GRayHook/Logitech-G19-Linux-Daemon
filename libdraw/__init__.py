# coding: utf-8
#
""" Helper for drawing"""
import os
import timeit
import PIL.Image as Img
import PIL.ImageDraw as Draw
import PIL.ImageFont as Font
#import libcdraw

class Frame(object):
    """docstring for Frame."""

    def __init__(self):
        super(Frame, self).__init__()
        self.__size_x = 320
        self.__size_y = 240
        self.__pixel_width = 2
        self.__map = [0] * (self.__size_x * self.__size_y * self.__pixel_width)

    def __get_column(self, column_i):
        """Get start point for column by column index"""
        return column_i * self.__size_y * self.__pixel_width

    def set_point(self, position, color):
        """Set pixel on map"""
        column = self.__get_column(position[0])
        index = column + position[1] * 2
        uint_16_color = self.__rgb_to_uint16(color)

        if len(color) > 3:
            old_pixel_uint16 = (self.__map[index] << 8) | self.__map[index + 1]
            uint_16_color = self.__uint16_apply_alpha(old_pixel_uint16, uint_16_color, color[3])

        self.__map[index] = self.__value_low(uint_16_color)
        self.__map[index + 1] = self.__value_high(uint_16_color)

    def get_map(self):
        """Getter for map"""
        return self.__map

    @staticmethod
    def __value_high(value=0):
        return value & 0xff

    @staticmethod
    def __value_low(value=0):
        return value >> 8 & 0xff

    @staticmethod
    def __rgb_to_uint16(color_rgb):
        """Converts a RGB value to 16bit highcolor (5-6-5).

        @return 16bit highcolor value in little-endian.

        """
        red_bits = color_rgb[0] * 2**5 / 255
        green_bits = color_rgb[1] * 2**6 / 255
        blue_bits = color_rgb[2] * 2**5 / 255

        red_bits = red_bits if red_bits <= 0b00011111 else 0b00011111
        green_bits = green_bits if green_bits <= 0b00111111 else 0b00111111
        blue_bits = blue_bits if blue_bits <= 0b00011111 else 0b00011111

        value_high = (red_bits << 3) | (green_bits >> 3)
        value_low = (green_bits << 5) | blue_bits
        return value_low << 8 | value_high


    @staticmethod
    def __uint16_apply_alpha(uint_16_color1, uint_16_color2, alpha):
        """Apply alpha channel for 16bit highcolor (5-6-5)."""


        # tik = timeit.default_timer()
        red1 = uint_16_color1 >> 3 & 0b00011111
        red2 = uint_16_color2 >> 3 & 0b00011111
        # print "red: " + str(timeit.default_timer() - tik)

        # tik = timeit.default_timer()
        green1 = ((uint_16_color1 & 0b00000111) << 3 | (uint_16_color1 >> 13)) & 0xff
        green2 = ((uint_16_color2 & 0b00000111) << 3 | (uint_16_color2 >> 13)) & 0xff
        # print "green: " + str(timeit.default_timer() - tik)


        # tik = timeit.default_timer()
        blue1 = uint_16_color1 >> 8 & 0b00011111
        blue2 = uint_16_color2 >> 8 & 0b00011111
        # print "blue: " + str(timeit.default_timer() - tik)

        red_bits = red2 * alpha + red1 * (1 - alpha)
        green_bits = green2 * alpha + green1 * (1 - alpha)
        blue_bits = blue2 * alpha + blue1 * (1 - alpha)

        value_high = (int(red_bits) << 3) | (int(green_bits) >> 3)
        value_low = (int(green_bits) << 5) | int(blue_bits)
        return value_low << 8 | value_high


class Drawer(object):
    """docstring for Drawer."""
    def __init__(self, frame):
        super(Drawer, self).__init__()
        self.__frame = frame

    def get_frame_data(self):
        """Getter for frame data"""
        return self.__frame.get_map()

    def draw_point(self, position, color_rgb):
        """Draw point on frame"""
        # while len(color_rgb) < 3:
        #     color_rgb = color_rgb + (0,)
        self.__frame.set_point(position, color_rgb)

    def draw_rectangle(self, position, size, color_rgb):
        """Draw rectangle on frame"""
        end_x = position[0] + size[0]
        end_y = position[1] + size[1]
        start_x = position[0]
        start_y = position[1]

        if len(size) == 6:
            start_x = size[2] if start_x < size[2] else start_x
            if start_x > size[4]:
                return
            end_x = size[4] if end_x > size[4] else end_x
            if end_x < size[2]:
                return
            start_y = size[3] if start_y < size[3] else start_y
            if start_y > size[5]:
                return
            end_y = size[5] if end_y > size[5] else end_y
            if end_y < size[3]:
                return

        for pixel_x in xrange(start_x, end_x):
            for pixel_y in xrange(start_y, end_y):
                self.draw_point([pixel_x, pixel_y], color_rgb)

    # DEPRECATED
    # def draw_line(self, position_start, position_end, color_rgb):
    #     """Draw line"""
    #     delta_y = position_end[1] - position_start[1]
    #     delta_x = position_end[0] - position_start[0]
    #     for offset_x in xrange(delta_x):
    #         offset_y = delta_y * offset_x / delta_x
    #         pixel_x = position_start[0] + offset_x
    #         pixel_y = position_start[1] + offset_y
    #         self.draw_point([pixel_x, pixel_y], color_rgb)

    def draw_image_from_file(self, position, size, filename):
        """Draw image frome file"""
        img = Img.open(filename)
        self.draw_image(position, size, img)

    def draw_image(self, position, size, img):
        """Draw image"""
        access = img.load()

        if img.size != (size[0], size[1]):
            img = img.resize((size[0], size[1]), Img.CUBIC)
            access = img.load()

        end = [position[0] + size[0], position[1] + size[1]]
        start = [position[0], position[1]]

        if len(size) == 6:
            start[0] = size[2] if start[0] < size[2] else start[0]
            if start[0] > size[4]:
                return
            end[0] = size[4] if end[0] > size[4] else end[0]
            if end[0] < size[2]:
                return
            start[1] = size[3] if start[1] < size[3] else start[1]
            if start[1] > size[5]:
                return
            end[1] = size[5] if end[1] > size[5] else end[1]
            if end[1] < size[3]:
                return

        for pixel_x in xrange(max(0, start[0]), min(320, end[0])):
            for pixel_y in xrange(max(0, start[1]), min(240, end[1])):
                # access_x = pixel_x - position[0]
                # access_y = pixel_y - position[1]
                if len(access[pixel_x - position[0], pixel_y - position[1]]) > 3:
                # if len(access[access_x, access_y]) > 3:
                    # alpha_channel = access[access_x, access_y][3]
                    alpha_channel = access[pixel_x - position[0], pixel_y - position[1]][3]
                    if alpha_channel == 0:
                        continue
                # color_rgb = access[access_x, access_y][0:3]
                color_rgb = access[pixel_x - position[0], pixel_y - position[1]][0:3]
                pixel_position = [pixel_x, pixel_y]
                self.draw_point(pixel_position, color_rgb)

    def draw_text_fitted(self, position, font_size, text):
        """Draw text"""
        font = Font.truetype(os.path.dirname(__file__) + "/11676.otf", font_size)
        height = font_size
        width = 0
        for i in xrange(len(text)):
            width += font.getsize(text[i])[0]
            if text[i] == '\n':
                width = 0
                height += font_size + 15
            if width > 320 - position[0]:
                text = text[:i-1] + '\n' + text[i-1:]
                width = 0
                height += font_size + 25
            if height > 240 - position[1]:
                text = text[:i-1]
                break
        img = Img.new("RGBA", (320, height), (0, 0, 0, 0))
        draw = Draw.Draw(img)
        draw.text([0, 0], text, (0, 0, 0), font=font)
        self.draw_image(position, [320, height], img)

    def draw_textline(self, position, font_size, text):
        """Draw text"""
        font = Font.truetype(os.path.dirname(__file__) + "/11676.otf", font_size)
        width = 0
        for i in xrange(len(text)):
            width += font.getsize(text[i])[0]
            if text[i] == '\n' or width > 320 - position[0]:
                text = text[:i-1]
                break
        img = Img.new("RGBA", (320, font_size), (0, 0, 0, 0))
        draw = Draw.Draw(img)
        draw.text([0, 0], text, (0, 0, 0), font=font)
        self.draw_image(position, [320, font_size], img)





if __name__ == '__main__':
    print "Пошёл на хуй"
