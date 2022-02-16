import os
import subprocess

from typing import List

import sysconfig

#I was wrong about the below! (although at the time maybe I was right?
# ###  distutils is better than setuptools for this use case, I've been
# ### debating this all night, as it is more basic;
# ### however if distutils is removed then there will be a problem.
import setuptools.errors as errors
from setuptools.command.build_ext import build_ext

from .cemake_extension import CMakeExtension

__all__ = ['cmake_build_ext']

class cmake_build_ext(build_ext):
  #Don't call super as we need all custom behav
  def run(self): 
    if not self.extensions:
      return
    self.build_extensions()

  def check_extensions_list(self, extensions):
    """Ensures that the list of extensions (presumably provided by 
    setuptools.setup's ext_modules parameter) is valid. i.e. it is a list of
    CMakeExtension objects. As CMakeExtension is a subclass of 
    setuptools Extension class we do not support the old style that
    used a list of 2-tuples which is supported by the origional Extension class
    
    Raise DistutilsSetupError if extensions is invalid anywhere;
    just returns otherwise
    """
    if not isinstance(extensions, list):
      raise errors.SetupError(
          "'ext_modules' argument must be a list of CMakeExtension instances "
          f"however ext_modules had type {type(extensions)}"
          )

    if not all(map(lambda ext: isinstance(ext, CMakeExtension), extensions)):
      raise errors.SetupError(
          "Each element of 'ext_modules' must be an instance of "
          "the CMakeExtension class"
          )

  def get_outputs(self) -> List[str]:
    # From super implementation:
    """ Sanity check the 'extensions' list -- can't assume this is being 
    done in the same run as a 'build_extensions()' call (in fact, we can
    probably assume that it *isn't*!).
    """

    self.check_extensions_list(self.extensions)


  def get_extension_build_directory(self, extension_name):
    # Uses "self.build_lib" etc as needed
    return os.path.dirname(
        os.path.abspath(
            self.get_ext_fullpath(extension_name)
            )
        )

  def build_extensions(self):
    # Ensure that CMake is present and working
    try:
      subprocess.run(['cmake', '--version'], check=True, stdout=subprocess.PIPE)
    except CalledProcessError:
      raise RuntimeError('Cannot find CMake executable')

    origional_package = self.package

    # Really useful to see what additional options we can use
    # print('***', *(self.user_options), sep="\n")
    # Same as python setup.py build_ext --help

    for extension in self.extensions:

      self.package = extension.package_name

      extension_dir = self.get_extension_build_directory(extension.name)
      config = 'Debug' if self.debug else 'Release'

      cmake_args = [
          f'-DCMAKE_BUILD_TYPE={config}',
          f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{config.upper()}={extension_dir}',
          # Needed for windows (more specifically .dll platforms).
          # It is safe to leave for all systems although will erroneously
          # add any .exe's created, which shouldn't exist anyway
          #
          # May remove for .so systems but without further testing it is
          # an unnecessary risk to remove 
          f'-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{config.upper()}={extension_dir}',
          # TODO: Explain better :- for python cmake extensions build
          # VV Remove from Cmake as option always on
          f'-DBUILD_PYTHON_EXTENSIONS=ON',
          f'-DPYTHON_EXTENSION={sysconfig.get_config_var("EXT_SUFFIX")}'
          ]
      if not os.path.exists(self.build_temp):
        os.makedirs(self.build_temp)

      # Config -> outputs in our temp dir
      subprocess.run(['cmake', extension.cmake_lists_dir] + cmake_args,
                     cwd=self.build_temp)
      
      # Build -> builds the config (AKA generated solution/makefiles) in
      #          our temp dir but outputs have already been setup in cmake_args
      subprocess.run(['cmake', '--build', '.', '--config', config],
                     cwd=self.build_temp)
