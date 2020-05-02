# USAGE
# python create_voice_msgs.py --conf config/config.json

from utils import Conf
from gtts import gTTS
import argparse
import pickle
import os


ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, 
                help="Path to the input configuration file")
args = vars(ap.parse_args())

conf = Conf(args["conf"])

print("[INFO] creating mp3 files...")

for name in conf["classes"]:
    print("[INFO] creating {}.mp3...".format(name))

    tts = gTTS(text="That's a {}".format(name), lang="{}-{}".format(
        conf["lang"], conf["accent"]))

    # save the speech generated as a mp3 file
    p = os.path.sep.join([conf["msgs_path"], "{}.mp3".format(name)])
    tts.save(p)
