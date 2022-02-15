import os
import subprocess

from typing import List

# distutils is better than setuptools for this use case, I've been
# debating this all night, as it is more basic;
# however if distutils is removed then there will be a problem.
from distutils.errors import DistutilsSetupError
from distutils.sysconfig import get_config_var
from distutils.command.build_ext import build_ext

from .cemake_extension import CMakeExtension

__all__ = ['cmake_build_ext']



class cmake_build_ext(build_ext):
  #TODO: decide whether I may as well override this too due to CMAKE usage
  def run(self): 
    if not self.extensions:
      return

    self.build_extensions()

    ## Ensure that CMake is present and working
    #try:
    #  subprocess.run(['cmake', '--version'], check=True, stdout=subprocess.PIPE)
    #except CalledProcessError:
    #  raise RuntimeError('Cannot find CMake executable')

    ## Really useful to see what additional options we can use
    ## print('***', *(self.user_options), sep="\n")
    #for extension in self.extensions:

    #  extension_dir = os.path.abspath(
    #      os.path.dirname(self.get_ext_fullpath(ext.name))
    #      )

    #  config = 'Debug' if self.debug else 'Release'
    #  #TODO: Warn windows users that config=Debug causes error on cmake --build

    #  cmake_args = [
    #      f'-DCMAKE_BUILD_TYPE={config}',
    #      f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{config.upper()}={extdir}',
    #      # Needed for windows (more specifically .dll platforms).
    #      # It is safe to leave for all systems although will erroneously
    #      # add any .exe's created, which shouldn't extis anyway
    #      #
    #      # May remove for .so systems but without further testing it is
    #      # an unnecessary risk to remove 
    #      f'-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{config.upper()}={extdir}',
    #      # TODO: Explain better :- for python cmake extensions build
    #      f'-DBUILD_PYTHON_EXTENSIONS=ON',
    #      f'-DPYTHON_EXTENSION={ext.library_extension}'
    #      ]

    #  if not os.path.exists(self.build_temp):
    #    os.makedirs(self.build_temp)

    #  # Config
    #  subprocess.run(['cmake', ext.cmake_lists_dir] + cmake_args,
    #                 cwd=self.build_temp)
    #  # Build
    #  subprocess.run(['cmake', '--build', '.', '--config', config],
    #                 cwd=self.build_temp)


  def check_extensions_list(self, extensions):
    """Ensures that the list of extensions (presumably provided by 
    setuptools.setup's ext_modules parameter) is valid. i.e. it is a list of
    CMakeExtension objects. As CMakeExtension is a subclass of 
    setuptools/distutils Extension class we do not support the old style that
    used a list of 2-tuples which is supported by the origional Extension class
    
    Raise DistutilsSetupError if extensions is invalid anywhere;
    just returns otherwise
    """
    if not isinstance(extensions, list):
      raise DistutilsSetupError(
          "'ext_modules' argument must be a list of CMakeExtension instances "
          f"however ext_modules had type {type(extensions)}"
          )

    if not all(map(lambda ext: isinstance(ext, CMakeExtension), extensions)):
      raise DistutilsSetupError(
          "Each element of 'ext_modules' must be an instance of "
          "the CMakeExtension class"
          )

  #TODO: implement ???
  def get_outputs(self) -> List[str]:
    # From super implementation:
    # Sanity check the 'extensions' list -- can't assume this is being
    # done in the same run as a 'build_extensions()' call (in fact, we
    # can probably assume that it *isn't*!).
    self.check_extensions_list(self.extensions)


  def get_extension_build_directory(self, extension_name):
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
    for extension in self.extensions:
      self.package = extension.package_name

      extension_dir = self.get_extension_build_directory(extension.name)

      config = 'Debug' if self.debug else 'Release'
      #TODO: Warn windows users that config=Debug causes error on cmake --build

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
          f'-DBUILD_PYTHON_EXTENSIONS=ON',
          f'-DPYTHON_EXTENSION={get_config_var("EXT_SUFFIX")}'
          ]

      if not os.path.exists(self.build_temp):
        os.makedirs(self.build_temp)

      # Config
      subprocess.run(['cmake', extension.cmake_lists_dir] + cmake_args,
                     cwd=self.build_temp)
      # Build
      subprocess.run(['cmake', '--build', '.', '--config', config],
                     cwd=self.build_temp)
