from __future__ import print_function
import os
import sys

import natlang as nl
import natlang.model.taggerPOS as _tagger
from natlang._support.general import getPTPath
pretrainedLang = {
    "en": {
        "url": None,
        "saved": "/en.save",
    },
}
pretrainPath = getPTPath("/tagger/pos")


def Tagger(lang="en", savedModel=None):
    if savedModel is None:
        if lang not in pretrainedLang:
            raise ValueError("[ERROR]: selected language does not have " +
                             "official pretrained models")
            return None
        # Using pretrained model here
        savedModel = pretrainPath + pretrainedLang[lang]["saved"]
        if not os.path.isdir(savedModel):
            # Download the model
            raise NotImplementedError
    tagger = _tagger.Tagger()
    if not os.path.isdir(savedModel):
        raise ValueError("[ERROR]: selected savedModel doesn't exist")
    tagger.load(savedModel)
    return tagger
