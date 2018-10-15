import format
import unittest
import setuptools


modules = {
    format.tree,
    format.conll,
    format.AMR,
    format.pyCode
}


def testSuite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite
    for module in modules:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


if __name__ == "__main__":
    setuptools.setup(
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        install_requires=[
              'jieba',
              'progressbar'
        ],
        test_suite='setup.testSuite'
    )
