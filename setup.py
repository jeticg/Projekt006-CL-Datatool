import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="datatool",
    version="0.3",
    author="Jetic Gu, Rory Wang",
    author_email="jeticg@sfu.ca",
    description="NLP data processing tools",
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
