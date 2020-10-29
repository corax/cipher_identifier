#!/usr/bin/python
import os
import re
import cv2
import requests
import pathlib
import numpy as np

BASE_PATH = "{}/ciphers".format(pathlib.Path(__file__).resolve().parents[1].absolute())
BASE_URL = "https://www.dcode.fr"
HOME_MESSAGE = "dCode</a> offers tools to win for sure, for example the <"

def crop_image(img):
    # https://stackoverflow.com/a/49907762
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = 255*(gray < 128).astype(np.uint8) # To invert the text to white
    coords = cv2.findNonZero(gray) # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords) # Find minimum spanning bounding box
    rect = img[y:y+h, x:x+w] # Crop the image - note we do this on the original image
    return rect

def download_cipher_images(cipher):
    cipher_base_path = "{}/{}".format(BASE_PATH, cipher)
    cipher_images_path = "{}/images".format(cipher_base_path)

    # Find the images
    url = requests.utils.requote_uri("{}/{}".format(BASE_URL, cipher))
    print("Trying to look up cipher URL:", url)
    r = requests.get(url, headers={"User-agent": "scrape"})
    content = r.content.decode()

    # Check if the cipher is valid
    if HOME_MESSAGE in content:
        print("[ERROR] Could not find a URL for cipher '{}'".format(cipher))
        print("Tried URL:", url)
        exit(1)

    js_string = re.findall(r'\<script\>\$\.cryptoarea\.path \= \'(.*?)\<\/script\>', content)
    if len(js_string) == 0:
        print("[ERROR] Could not extract the JS to find the images")
        exit(1)

    string_split = js_string[0].split(";")

    # Extract out images url, i.e. https://www.dcode.fr/tools/stargate-ancients/images
    images_url = string_split[0][:-1]

    # Find the array of char(x).
    match = re.search(r'\[(.*?)\]', string_split[1]).group(1)
    # Find all char(x).png (pictures of the symbols).
    chars = re.findall(r'\((.*?)\)', match)

    # Create directory if it doesn't exist
    os.makedirs(cipher_images_path, exist_ok=True)

    images_downloaded = set()
    for char in chars:
        i = int(char)

        # Don't download images twice
        if i in images_downloaded:
            continue

        image_filename = "char({}).png".format(i)
        image_path = "{}/{}".format(cipher_images_path, image_filename)
        image_url = "{}/{}".format(images_url, image_filename)
        print("Fetching image: '{}' and saving it to {}".format(image_filename, cipher_images_path))
        r = requests.get(image_url)

        if r.status_code != 200:
            print("[ERROR] Something went wrong when downloading image, status code: {}".format(r.status_code))
            exit(1)

        # Read the image into CV2
        nparr = np.frombuffer(r.content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        # Crop the image (remove borders i.e.)
        image = crop_image(image)

        # For debugging, show the image
        """
        cv2.imshow('image',image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        exit(0)
        """

        cv2.imwrite(image_path, image)

        images_downloaded.add(i)

    print("Done!")

"""
# Download all from ciphers.txt
with open("ciphers.txt") as f:
    ciphers = f.read().splitlines()
    for cipher in ciphers:
        download_cipher_images(cipher)
"""

# TODO: use arguments instead?
# Get info from input, example: ancients-stargate-alphabet
print("Which cipher do you want to download images for?")
print("Example: ancients-stargate-alphabet")
print("From URL: https://www.dcode.fr/ancients-stargate-alphabet")
cipher = input("> ")
download_cipher_images(cipher)
