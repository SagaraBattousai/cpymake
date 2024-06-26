""" This module contains setuptools extension subclasses to allow 
describing CMake builds to generate libraries for python extension 
modules

"""
# import os.path
from dataclasses import dataclass

from setuptools import errors
from setuptools.extension import Extension as _Extension


@dataclass
class Extension(_Extension):
    """This is the main ``Extension`` class for describing cmake python
    extension module builds.

    Attributes
    ----------
    package_name : str
      The name of the package, in dotted notation
      i.e. outterpackage.innerpackage, that cmake describes, all
      extension modules are grouped together under the package if
      ``inplace`` is True and the global ``--inplace`` flag is set
      (in pyproject.toml etc). Otherwise all extension modules are
      in the root of the project build.

    target : str
      Target to build. Each Extension must be a single target.

    cmake_lists_root_dir : str,
      Absolute path to root CMakeLists.txt. This *MUST* be an absolute path as
      setuptools, pip and build use temp directories and so relative paths will fail.
      If using multiple CMakeExtension's, for
      example in order to have multiple extension modules in different
      packages ensure you use different CMakeLists.txt in different
      directories. This may change if it causes extra work however for
      now it seems acdeptable.


    generator: str | None, default None
        generator to use when building. If None (the default) then camke isn't
        passed the -G flag and the default generator for the host system will
        be used.

    """

    #NOTE: Unused for now:
    # targets: list[str] | None, default: None
    #   List of targets to build. If None (the default) then no targets are
    #   specified and camke --build is ran without the --target option.

    # Could make dataclass
    def __init__(  # pylint: disable=keyword-arg-before-vararg
        self,
        package_name: str,
        # A Must be specified inorder to not build unrequired code
        # B Each Extension must be a single target (is that bad?)
        target: str,
        cmake_lists_root_dir: str = ".", # Defaults to project root dir
        # targets: list[str] | None = None,  # Could make args?
        generator: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(name=package_name, sources=[], *args, **kwargs)
        # self.package_name = package_name
        self.cmake_lists_root_dir = cmake_lists_root_dir
        self.target = target
        # self.targets = targets
        self.generator = generator
