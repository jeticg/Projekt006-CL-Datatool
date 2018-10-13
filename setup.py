# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Setup
# Simon Fraser University
# Jetic Gu
#
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="natlang",
    version="0.3.a4",
    author="Jetic Gū, Rory Wang",
    author_email="jeticg@sfu.ca",
    description="Natural language data loading tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jeticg/datatool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
