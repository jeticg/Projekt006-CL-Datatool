# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Text loader
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
from tree import load
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    return [line.strip().split() for line in open(os.path.expanduser(file))][
        :linesToLoad]
