import os
import sys
import inspect


currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
if os.path.dirname(parentdir) not in sys.path:
    sys.path.insert(0, os.path.dirname(parentdir))
