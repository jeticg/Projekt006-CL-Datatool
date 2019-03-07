from __future__ import print_function
import os
import sys

import natlang as nl
import natlang.model.tagger as _tagger
pretrainedLang = {
    "en": {
        "url": None,
        "saved": "/ner/en.save",
    },
}
if os.path.expandvars("$NATLANG_MODEL") == "$NATLANG_MODEL":
    nlPath = os.path.expanduser("~/.natlang")
else:
    nlPath = os.path.expandvars("$NATLANG_MODEL")
pretrainPath = nlPath + "/tagger"
try:
    os.makedirs(pretrainPath + "/tagger")
except OSError as e:
    pass


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
