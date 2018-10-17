# natlang: Natural Language Data Loading Tools
master: [![Build Status](https://travis-ci.com/jeticg/datatool.svg?branch=master)](https://travis-ci.com/jeticg/datatool)
dev: [![Build Status](https://travis-ci.com/jeticg/datatool.svg?branch=dev)](https://travis-ci.com/jeticg/datatool)

Data loader/common data structures and other tools

Most of the code are Python2/3 compatible.
For the version of python for specific modules, please check the second line of
each source file.

## 0. Usage

Place this entire repo somewhere in your project, or add it to your python
library.

## 1. Format

All supported formats are placed under `src/format`.
Currently the following formats are tested:

1. `txt`: simple text format. Sentences are separated by `\n`, tokens/words are
separated by whitespace.

2. `tree`: constituency tree format. Run `python -i format/tree.py` to play
around.

3. `semanticFrame`: Propbank/Nombank frame loader. Returns bundles of frames
for analysis.

4. `AMR`: Abstract Meaning Representation. Run `python -i format/AMR.py` to
play around.

### 1.1 Recommended Functions

For formats supporting being loaded from a file, one should implement a `load`
function in the format file (see 2.1).

For formats supporting being exported, each instance of that format should have
an `export` method that outputs a string.

## 2. Loader

### 2.1 Individual Loader

Each format has its own loader.
It is defined as `format.FORMAT.load`.
The `load` function has the following interface:

    def load(file, linesToLoad=sys.maxsize)

At test time, the `load` function would be expected to parse the file
description and read from it.
It will return the first `linesToLoad` entries as a list.

For example, if one wishes to use load a file in constituency tree format (see
example in `tests/sampleTree.txt`), one could do the following:

    from datatool.format import tree
    x = tree.load("datatool/tests/sampleTree.txt")

### 2.2 Class `ParallelDataLoader`

This class allows one to load parallel corpora (L1, L2) in any format.
You can specify the format for L1 and L2 side separately.

    from datatool.loader import ParallelDataLoader
    loader = ParallelDataLoader(srcFormat='txtOrTree', tgtFormat='txtOrTree')

Here, `'txtOrTree'` is the default value for `srcFormat` and `tgtFormat`.
Note that under the `format` folder, except for data structures for specific
formats, there are also mere loaders and `'txtOrTree'` is one that can handle
both `tree` and `txt`.

After initialising the loader, one can just go ahead and run:

    loader.load(fFile, eFile, linesToLoad)

The loader will automatically align the parallel text and output a list of
tuples, each containing a single entry in L1 and L2.
Entries with either L1 or L2 being `None` or of length 0 will be omitted.

## 3. Exporter

Usage:

    from datatool.exporter import exportToFile, RealtimeExporter

### 3.1 Function `exportToFile`

Export a `txt` format dataset or `tree` format dataset (not single entry, but
rather a dataset) to file.

### 3.2 Class `RealtimeExporter`

The code is pretty self-explanatory.
If the export function of a specific format takes quite a bit of time, this
method is recommended.
