from PIL import Image
import numpy as np

img = Image.open("images/GOPR0042.JPG")
data = np.asarray(img)

stopper = 0
for pixel in data[:][:]:
    if stopper < 10:
        print(pixel)
        stopper += 1
