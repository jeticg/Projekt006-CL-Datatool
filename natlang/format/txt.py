# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Text loader
# Simon Fraser University
# Jetic Gu
#
#
from __future__ import absolute_import
import os
import sys
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    return [line.strip().split() for line in open(os.path.expanduser(file))][
        :linesToLoad]
