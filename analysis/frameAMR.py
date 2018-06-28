# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Provide a brief analysis of propbank-frame-arg-descr.txt from AMR2.0 dataset
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
import inspect
import argparse

currentdir =\
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from support.fileIO import loadAMRFrame

if __name__ == '__main__':
    ap = argparse.ArgumentParser(
        description="""AMR 2.0 Frame Analyser""")
    ap.add_argument(
        "filename", metavar='FILENAME',
        help="AMR 2.0 frame file")
    args = ap.parse_args()
    frames = loadAMRFrame(args.filename)
    print("----- Statistics -----")
    print("# of frames:          ", len(frames))
    args = {}
    for _, a in frames:
        for ar in a:
            if ar not in args:
                args[ar] = 1
            else:
                args[ar] += 1
    print("# of different ARGs:  ", len(args))
    for arg in args:
        print("# of frames with " + arg + ":", args[arg])
