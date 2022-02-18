import pathlib
import subprocess
import sysconfig

from typing import List


import setuptools.errors as errors
from setuptools.command.build_ext import build_ext
from .cemake_extension import CMakeExtension

__all__ = ['cmake_build_ext']

class cmake_build_ext(build_ext):
  def __init__(self, dist):
    super().__init__(dist)
    self.extension_suffix = sysconfig.get_config_var("EXT_SUFFIX")

  def finalize_options(self):
    """ For initialising variables once the other options have been
    finalised

    """
    
    super().finalize_options()
    self.build_temp_path = pathlib.Path(self.build_temp)

  #Don't call super as we need all custom behaviour
  def run(self):
    if not self.extensions:
      return
    
    self.build_extensions()
    # VV Happens automatically as inplace automatically modifys build dir
    # to be inplace :D -> wasted time sad tho.
    #if self.inplace:
    #  self.copy_extensions_to_source()

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
    """ This function gets the full path to the build directory as 
        specified by "self.build_lib" or the source directory if
        inplace is set.

    """
    extension_path = self.get_ext_fullpath(extension_name)
    return pathlib.Path(extension_path).resolve().parent

  def build_extensions(self):
    # Ensure that CMake is present and working. Was going to extract
    # but I think that that is unneccisary
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
      extension_suffix = sysconfig.get_config_var("EXT_SUFFIX")
      config = 'DEBUG' if self.debug else 'RELEASE'

      cmake_args = [
          f'-DCMAKE_BUILD_TYPE={config}',
          f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{config}={extension_dir}',
          # Needed for windows (more specifically .dll platforms).
          # It is safe to leave for all systems although will erroneously
          # add any .exe's created, which shouldn't exist anyway
          #
          # May remove for .so systems but without further testing it is
          # an unnecessary risk to remove 
          f'-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{config}={extension_dir}',
          f'-DPYTHON_EXTENSION_SUFFIX={extension_suffix}'
          ]

      if not self.build_temp_path.exists():
        self.build_temp_path.mkdir(parents=True)

      # Config -> outputs in our temp dir
      subprocess.run(['cmake', extension.cmake_lists_dir] + cmake_args,
                     cwd=self.build_temp)
      
      # Build -> builds the config (AKA generated solution/makefiles) in
      #          our temp dir but outputs have already been setup in cmake_args
      subprocess.run(['cmake', '--build', '.', '--config', config],
                     cwd=self.build_temp)
