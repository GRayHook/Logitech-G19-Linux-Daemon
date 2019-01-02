#!/usr/bin/python
from distutils.core import setup
from distutils.extension import Extension
examplemodule = Extension(name="libcdraw", sources=['cdraw.c', ])
setup(name="libcdraw", ext_modules=[examplemodule])
