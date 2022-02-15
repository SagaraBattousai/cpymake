""" This module contains distutils extension subclasses to allow describing
CMake builds to generate libraries for python extension modules

"""

import os

# distutils is better than setuptools for this use case, I've been
# debating this all night, as it is more basic;
# however if distutils is removed then there will be a problem.
from distutils.extension import Extension

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

  inplace : bool, default: True
    Whether to place built extensions in a the package passed by 
    ``package_name`` or put them in the root of the project build.

  """
  def __init__(self, package_name:str, cmake_lists_dir:str='.',
               inplace:bool=True, **kwargs):
    Extension.__init__(self, name='', sources=[], **kwargs)
    
    self.package_name = package_name
    self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)

