import numpy as np
import cv2
import time
import math


class ImageProcessor:
    def __init__(self, image_path):
        #self.img = cv2.imread(image_path)
        self.img = image_path
        self.gray_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

        # pixels that have lower value than 245 turns into black, others to white (higher number -> smaller area)
        # Image is gray scale so its values are form 0 (black) to 255 (white)
        _, self.direct_light = cv2.threshold(self.gray_img, 245, 255, cv2.THRESH_BINARY)
        M = cv2.moments(self.direct_light)
        try:
            self.lighting_center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        except ZeroDivisionError:
            self.lighting_center = (0, 0)

        # direct light + surrounding color
        _, self.color_light = cv2.threshold(self.gray_img, 180, 255, cv2.THRESH_BINARY)

        self.surrounding_pixels = self._get_surrounding_pixels_but_not_direct_light(self.direct_light, self.color_light)
        self.avg_bgr = self._calculate_avg_color_of_surroundings(self.surrounding_pixels)

    def _get_surrounding_pixels_but_not_direct_light(self, direct_light, surrounding_light):
        # subtraction of pixels between surrounding light and direct light
        pixels_of_direct_light = self._get_coords_of_white_pixels(direct_light)
        self._paint_pixels(pixels_of_direct_light, surrounding_light, 0)
        return self._get_coords_of_white_pixels(surrounding_light)

    def _calculate_avg_color_of_surroundings(self, arr_2d):
        counter = 0
        color_sum = [0, 0, 0]
        for x, y in arr_2d:
            if self._calculate_distance_from_center(y, x) < 100:
                rgb = self.img[x, y]
                color_sum[0] += rgb[0]
                color_sum[1] += rgb[1]
                color_sum[2] += rgb[2]
                counter += 1
        if counter == 0:
            return [0, 0, 0]
        return [x // counter for x in color_sum]  # get average

    def _calculate_distance_from_center(self, x, y):
        return math.sqrt((self.lighting_center[0] - x)**2 + (self.lighting_center[1] - y)**2)

    def _get_coords_of_white_pixels(self, arr):
        return np.argwhere(arr == 255)

    def _paint_pixels(self, src_arr_2d, dst_arr_2d, color):
        for x, y in src_arr_2d:
            dst_arr_2d[x, y] = color

    def show_result(self):
        cv2.imshow("Original", self.img)
        self._paint_pixels(self.surrounding_pixels, self.img, self.avg_bgr)
        cv2.imshow("Processed part", self.color_light)
        cv2.imshow("Painted Original", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def get_avg_pixel_color(self):
        rgb = [self.avg_bgr[2], self.avg_bgr[1], self.avg_bgr[0]]
        return self.avg_bgr, self.classify_rgb(rgb)

    def classify_rgb(self, rgb):
        colors = {
            "red": [255, 0, 0],
            "green": [0, 255, 0],
            "blue": [0, 0, 255]
        }
        distances = {k: self._get_manhattan_distance(v, rgb) for k, v in colors.items()}
        color = min(distances, key=distances.get)
        return color

    def _get_manhattan_distance(self, x, y):
        return abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])


class ClassificationTable:
    # some ugly ass code
    def __init__(self):
        import os
        from beautifultable import BeautifulTable
        table = BeautifulTable(max_width=200)
        data = []
        rows = set()
        all_colors = set()
        directory = "TestImages/"
        for file in os.listdir(directory):
            if file.endswith(".jpg"):
                file_settings = file[:-4].split("_")
                predicted_color = ImageProcessor(os.path.join(directory, file)).get_avg_pixel_color()[1]
                all_colors.add(file_settings[0])
                rows.add(int(file_settings[2][0]))
                # distance, direction, real color, predicted color
                data.append((file_settings[2], file_settings[1], file_settings[0], predicted_color))
        table.column_headers = [" "] + list(all_colors)
        second_row = [" "]
        columns = {}
        for color in table.column_headers[1:]:
            columns[color] = {"direct": [""] * (max(rows)+1), "indirect": [""] * (max(rows)+1)}
            second_row.append("direct | indirect")
        table.append_row(second_row)
        for distance, direction, real_color, predicted_color in data:
            columns[real_color][direction][int(distance[0])] = predicted_color
        rows = sorted(rows)
        for i, distance in enumerate(rows):
            row = [str(distance) + " m"]
            for color in table.column_headers[1:]:
                row.append(columns[color]["direct"][rows[i]] + " | " + columns[color]["indirect"][rows[i]])
            table.append_row(row)
        print(table)


if __name__ == '__main__':
    imgp = ImageProcessor("TestImages/red_direct_1m.jpg")
    print(imgp.get_avg_pixel_color())
    imgp.show_result()
    classTable = ClassificationTable()

