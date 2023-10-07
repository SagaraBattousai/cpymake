""" This module contains setuptools extension subclasses to allow 
describing CMake builds to generate libraries for python extension 
modules

"""

import pathlib
from dataclasses import dataclass

from setuptools.extension import Extension


@dataclass
class CeMakeExtension(Extension):
    """This is the main ``Extension`` class for describing cmake python
    extension module builds.

    Attributes
    ----------
    package_name : str
      The name of the package, in dotted notation
      i.e. outterpackage.innerpackage, that cmake describes, all
      extension modules are grouped together under the package if
      ``inplace`` is True and the global ``--inplace`` flag is set
      (in pyproject.toml etc); both default to True. Otherwise all extension
      modules are in the root of the project build.

    cmake_lists_root_dir : str, default: "."
      Path to root CMakeLists.txt, the default assumes it is in the same
      directory as set setup.py. If using multiple CMakeExtension's, for
      example in order to have multiple extension modules in different
      packages ensure you use different CMakeLists.txt in different
      directories. This may change if it causes extra work however for
      now it seems acdeptable.

    targets: list[str] | None, default: None
      List of targets to build. If None (the default) then no targets are
      specified and camke --build is ran without the --target option.

    generator: str | None, default None
        generator to use when building. If None (the default) then camke isn't
        passed the -G flag and the default generator for the host system will
        be used.

    """

    # Could make dataclass
    def __init__(
        self,
        package_name: str,
        *args,
        cmake_lists_root_dir: str = ".",
        targets: list[str] | None = None,  # Could make args?
        generator: str | None = None,
        **kwargs,
    ):
        super().__init__(name=package_name, sources=[], *args, **kwargs)  # type:ignore
        self.package_name = package_name
        self.cmake_lists_root_dir = pathlib.Path(cmake_lists_root_dir).resolve()
        self.targets = targets
        self.generator = generator
