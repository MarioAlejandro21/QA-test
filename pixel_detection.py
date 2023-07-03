from skimage.color import rgb2lab, deltaE_cie76, rgb2gray
from skimage.io import imread
import numpy as np


def delta_less_than(reference_path: str, test_path: str, max_delta):
    ref_img = rgb2lab(imread(reference_path))
    test_img = rgb2lab(imread(test_path))


    deltas = deltaE_cie76(ref_img, test_img).flatten()
    print(max(deltas))

    return not np.any(deltas >= max_delta)





