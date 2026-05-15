import cv2
import numpy as np
import random


# base class for different types of changes we can make to an image
class Alteration:
    def __init__(self):
        self.min_size = 40
        self.max_size = 80

    def get_random_region(self, img_height, img_width):
        w = random.randint(self.min_size, self.max_size)
        h = random.randint(self.min_size, self.max_size)
        x = random.randint(0, img_width - w - 1)
        y = random.randint(0, img_height - h - 1)
        return x, y, w, h

    def apply(self, image, x, y, w, h):
        return image


# shift the colour of a region
class ColourShift(Alteration):
    def apply(self, image, x, y, w, h):
        img = image.copy()
        region = img[y:y+h, x:x+w].astype(np.int16)
        region[:, :, 2] = np.clip(region[:, :, 2] + 60, 0, 255)
        region[:, :, 0] = np.clip(region[:, :, 0] - 30, 0, 255)
        img[y:y+h, x:x+w] = region.astype(np.uint8)
        return img


# blur a region
class BlurPatch(Alteration):
    def apply(self, image, x, y, w, h):
        img = image.copy()
        img[y:y+h, x:x+w] = cv2.GaussianBlur(img[y:y+h, x:x+w], (21, 21), 0)
        return img


# make a region darker
class BrightnessChange(Alteration):
    def apply(self, image, x, y, w, h):
        img = image.copy()
        region = img[y:y+h, x:x+w].astype(np.int16)
        img[y:y+h, x:x+w] = np.clip(region - 60, 0, 255).astype(np.uint8)
        return img


# rotate the hue in a region
class HueRotation(Alteration):
    def apply(self, image, x, y, w, h):
        img = image.copy()
        region = img[y:y+h, x:x+w]
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV).astype(np.int16)
        hsv[:, :, 0] = (hsv[:, :, 0] + 40) % 180
        img[y:y+h, x:x+w] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return img


class ImageProcessor:
    def __init__(self):
        self.original = None
        self.modified = None
        self.diff_regions = []

    def load(self, path):
        img = cv2.imread(path)
        if img is None:
            return False

        h, w = img.shape[:2]
        scale = min(580 / w, 480 / h, 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        self.original = img
        self.modified, self.diff_regions = self.make_modified(img)
        return True

    def regions_overlap(self, r1, r2):
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        # check if rectangles overlap
        if x1 + w1 < x2 or x2 + w2 < x1:
            return False
        if y1 + h1 < y2 or y2 + h2 < y1:
            return False
        return True

    def make_modified(self, img):
        h, w = img.shape[:2]
        modified = img.copy()

        alteration_types = [ColourShift(), BlurPatch(), BrightnessChange(), HueRotation()]
        random.shuffle(alteration_types)

        placed = []
        regions = []

        i = 0
        while len(regions) < 5 and i < 500:
            alt = random.choice(alteration_types)
            x, y, rw, rh = alt.get_random_region(h, w)
            rect = (x, y, rw, rh)

            # check overlapping with existing ones
            overlap = False
            for p in placed:
                if self.regions_overlap(rect, p):
                    overlap = True
                    break

            if not overlap:
                modified = alt.apply(modified, x, y, rw, rh)
                placed.append(rect)
                regions.append({
                    'x': x, 'y': y, 'w': rw, 'h': rh,
                    'found': False
                })
            i += 1

        return modified, regions