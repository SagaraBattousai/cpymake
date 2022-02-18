""" This module contains setuptools extension subclasses to allow describing
CMake builds to generate libraries for python extension modules

"""

import pathlib

from setuptools.extension import Extension

__all__ = ['CMakeExtension']

class CMakeExtension(Extension):
  """This is the main ``Extension`` class for describing cmake python extension
  module builds.

  Attributes
  ----------
  package_name : str
    The name of the package, in dotted notation i.e. outterpackage.innerpackage,
    that cmake describes, all extension modules are grouped together under
    the package if ``inplace`` is True and the global ``--inplace`` falg
    is set (in setup.cfg etc); both default to True.
    Otherwise all extension modules are in the root of the project build.

  cmake_lists_dir : str, default: "."
    Path to root CMakeLists.txt, the default assumes it is in the same
    directory as set setup.py. If using multiple CMakeExtension's, for example
    in order to have multiple extension modules in different packages ensure
    you use different CMakeLists.txt in different directories. This may change
    if it causes extra work however for now it seems acdeptable.

  """
  def __init__(self, package_name:str, cmake_lists_dir:str='.',
               *args, **kwargs):
    #May need to do something clever with name, inc adding to constructor.
    super().__init__(name='', sources=[], *args, **kwargs)
    # Could leave off and just add to cfg for build_ext package
    #Ah what if even better we say module as there are multiple modules per
    # package, but then wouldnt you need more CMakeLists???
    self.package_name = package_name 
    self.cmake_lists_dir = pathlib.Path(cmake_lists_dir).resolve()
