from argparse import ArgumentParser
import cv2
import os
import logging
import traceback
import shutil
from tqdm import tqdm, tqdm_gui
import time
import numpy as np
import multiprocessing
from multiprocessing import Pool, cpu_count
from p_tqdm import p_map
import sys
import utils
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array

def run(paths):    
    src, out = paths
    if not os.path.exists(out):
        img = cv2.imread(src)
        img = cv2.resize(img, (255, 255))
        
        faces = []
        croppedImages = []
        
        for ith_face, box in enumerate(bbox): 
            x,y,w,h,_ = list(map(int, box))
            imgCrop = img[y:y+h,x:x+w]
            croppedImages.append(imgCrop)
            face = cv2.cvtColor(imgCrop, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)
            face = np.expand_dims(face, axis=0)
            faces.append(face)
                
            preds = maskNet.predict(faces)
            print(preds)
            saveImg = True
            if CROP_FACES:
                if DUPLICATE:
                    if MOVE_IMGS:
                        shutil.move(src, out)
                    else:
                        utils.copyFile(src, out)

                if not imgCrop.empty():
                        out += f"face_{str(ith_face)}.jpg"
                        cv2.imwrite(out, imgCrop)
            
            if MOVE_IMGS:
                shutil.move(src, out)
            else:
                utils.copyFile(src, out)
            utils.write("Filtered images: {} | Saved images percentage:  {}".format(num_imgs_filtered, saved_imgs_percentage))
            
def main(args):
    pathsGenerator = utils.yieldPaths(args["INPUT_BASE_DIR"], args["OUTPUT_PATH"], flat = FLAT)
    if not FLAT:
        utils.copyDirectoryStructure(args["INPUT_BASE_DIR"], args["OUTPUT_PATH"])
    
    logging.info("Starting...")
    with tqdm(total=NUM_FILES, 
                    desc="                                                ", 
                    unit="Images") as pbar:
        pass
            # percentage = round((i/NUM_FILES)*100, 3)
            # utils.write(f"Images processed:{i} | Percentage: {percentage}%")

if __name__ == '__main__':
    # Initialize parser
    parser = ArgumentParser(
        description="Script for detecting faces in a given folder and its subdirectories"
    )
    
    parser.add_argument("-in", "--input-path", 
                        type=str,
                        required=True,
                        dest="INPUT_BASE_DIR", 
                        help="Path to the directory where images or folders of images are\n")
    
    parser.add_argument("-out","--output-path",
                        type=str, 
                        required=True,
                        dest = "OUTPUT_PATH", 
                        help="Path of the folder where faces images will be saved\n")
    
    parser.add_argument("-move", "--move-kept-images", 
                        action="store_true",
                        default=False,
                        dest = "move_images",
                        help = "Whether to move kept images from [-in, --input-path] to [-out, --output-path] in such a way that in the remaining images in [-in --input-path] are the ones that did not apply the criteria.")

    parser.add_argument("-crop","--crop-faces", 
                        action='store_true',
                        dest="crop_faces",
                        default=False, 
                        help="Crop faces detected in images and save each one\n")
    
    parser.add_argument("-flat", "--same-out-dir",
                        action='store_true',
                        dest="save_in_same_output_folder",
                        default=False,
                        help="Whether to save all images in dirctory specified in -out --output-path and not imitate directory structure from the path specified in -indir --input-base-dir\n")

    parser.add_argument("-duplicate", "--duplicate-img-faces",
                        action="store_true", 
                        dest="duplicate_img_of_faces",
                        default=False, 
                        help="Whether to save the original images of the extracted faces also. Only valid if -crop --crop-faces is passed as argument")
    
    parser.add_argument("-model", "--classification-model", 
                        type=str,
                        dest = "classification_model", 
                        default="resources/model_with_1400_masked_samples.h5")
    args = vars(parser.parse_args())
    
    logging.basicConfig(level=logging.INFO)
    logging.info(" Preparing face detection model...")

    logging.info(" Preparing mask detection model...")
    maskNet = tf.keras.models.load_model(args["classification_model"], compile=False)
    
    DUPLICATE = args["duplicate_img_of_faces"]
    MOVE_IMGS = args["move_images"]
    FLAT = args["save_in_same_output_folder"]
    CROP_FACES= args["crop_faces"]
    NUM_FILES = utils.countFiles(args["INPUT_BASE_DIR"])
    NUM_CPUS = cpu_count()
    num_imgs_filtered = 0
    processed_imgs = 0 
    
    logging.info(f"{str(NUM_FILES)} files found")
    logging.info(f"Working with {NUM_CPUS} cpus")
    main(args)