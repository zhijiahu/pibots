from utils import Conf
from gtts import gTTS
import argparse
import pickle
import os

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
                help="Path to the input configuration file")
args = vars(ap.parse_args())

# load the configuration file and label encoder
conf = Conf(args["conf"])
print("[INFO] creating mp3 files...")

# loop over all class labels (i.e., names)

tts = gTTS(text=conf["msg_body"], lang="{}-{}".format(conf["lang"], conf["accent"]))

# save the speech generated as a mp3 file
p = os.path.sep.join([conf["msg_path"], "motion_detected.mp3".format()])
tts.save(p)
