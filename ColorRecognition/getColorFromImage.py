import numpy as np
import cv2


class ImageProcessor:
    def __init__(self, image_path):
        self.img = cv2.imread(image_path)
        self.gray_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

        # pixels that have lower value than 245 turns into black, others to white (higher number -> smaller area)
        # Image is gray scale so its values are form 0 (black) to 255 (white)
        _, self.direct_light = cv2.threshold(self.gray_img, 245, 255, cv2.THRESH_BINARY)
        # direct light + surrounding color
        _, self.color_light = cv2.threshold(self.gray_img, 140, 255, cv2.THRESH_BINARY)

        self.surrounding_pixels = self._get_surrounding_pixels_but_not_direct_light(self.direct_light, self.color_light)
        self.avg_bgr = self._calculate_avg_color_of_surroundings(self.surrounding_pixels)

    def _get_surrounding_pixels_but_not_direct_light(self, direct_light, surrounding_light):
        # subtraction of pixels between surrounding light and direct light
        pixels_of_direct_light = self._get_coords_of_white_pixels(direct_light)
        self._paint_pixels(pixels_of_direct_light, surrounding_light, 0)
        return self._get_coords_of_white_pixels(surrounding_light)

    def _calculate_avg_color_of_surroundings(self, arr_2d):
        color_sum = [0, 0, 0]
        for x, y in arr_2d:
            rgb = self.img[x, y]
            color_sum[0] += rgb[0]
            color_sum[1] += rgb[1]
            color_sum[2] += rgb[2]

        return [x // len(arr_2d) for x in color_sum]  # get average

    def _get_coords_of_white_pixels(self, arr):
        return np.argwhere(arr == 255)

    def _paint_pixels(self, src_arr_2d, dst_arr_2d, color):
        for x, y in src_arr_2d:
            dst_arr_2d[x, y] = color

    def show_result(self):
        self._draw_contours()
        cv2.imshow("Original", self.img)
        self._paint_pixels(self.surrounding_pixels, self.img, self.avg_bgr)
        cv2.imshow("Processed part", self.color_light)
        cv2.imshow("Painted Original", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def _draw_contours(self):
        _, contours, _ = cv2.findContours(self.color_light, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(self.img, contours, -1, (0, 0, 0), 1)

    def get_avg_pixel_color(self):
        rgb = [self.avg_bgr[2], self.avg_bgr[1], self.avg_bgr[0]]
        return rgb, self.classify_rgb(rgb)

    def classify_rgb(self, rgb):
        colors = {
            "red": [255, 0, 0],
            "green": [0, 255, 0],
            "blue": [0, 0, 255],
            "yellow": [255, 255, 0],
            "purple": [255, 0, 255],
            "orange": [255, 128, 0]
        }
        distances = {k: self.get_manhattan_distance(v, rgb) for k, v in colors.items()}
        color = min(distances, key=distances.get)
        return color

    def get_manhattan_distance(self, x, y):
        return abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])


if __name__ == '__main__':
    imgp = ImageProcessor("TestImages/blue.jpg")
    print(imgp.get_avg_pixel_color())
    imgp.show_result()

