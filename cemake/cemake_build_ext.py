""" 
cemake's build_ext command for building a python C/C++ extension using
cemakes Extension class 
"""

import pathlib
import subprocess
import sysconfig

from typing import List

from setuptools import errors
from setuptools.command.build_ext import build_ext
from cemake.cemake_extension import CeMakeExtension


class CeMakeBuildExt(build_ext):
    """Cemake's build_ext class that can be used as a plugin for setuptools
    to build extension modules that use CMake as their
    build (generator) system
    """

    def __init__(self, dist):
        super().__init__(dist)
        self.extension_suffix = sysconfig.get_config_var("EXT_SUFFIX")

    # override
    def initialize_options(self):
        """Set (or reset) build_temp_path. Note fields set here may be
        overwritten during the build
        """
        super().initialize_options()
        self.build_temp_path = None

    # override
    def finalize_options(self):
        """For initialising variables once the other options have been
        finalised
        """
        # print("Before:", self.extensions[0].cmake_lists_root_dir)
        super().finalize_options()
        if self.build_temp_path is None:
            self.build_temp_path = (  # pylint: disable=attribute-defined-outside-init
                pathlib.Path(self.build_temp).resolve()
            )

    # Don't call super as we need all custom behaviour
    # override
    def run(self):
        # 'self.extensions', as supplied by setup.py, is a list of
        # Extension instances.
        if not self.extensions:
            return

        # Ensure that CMake is present and working. Was going to extract
        # but I think that that is unneccisary
        try:
            subprocess.run(["cmake", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError as cpe:
            raise RuntimeError("Cannot find CMake executable") from cpe

        self.build_extensions()
        # VV Happens automatically as inplace automatically modifys build dir
        # to be inplace :D -> wasted time sad tho.
        # if self.inplace:
        #  self.copy_extensions_to_source()
        # ^^ self.inplace is set in super().finalize_options() to be true
        # when self.editable_mode is True

    # override
    def build_extensions(self):
        # origional_package = self.package

        # Really useful to see what additional options we can use
        # print('***', *(self.user_options), sep="\n")
        # Same as python setup.py build_ext --help

        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)

        print(self.inplace)

        for extension in self.extensions:
            # Looks dodgy but it's been years since I made this so...
            # Actually maybe not...
            self.package = (  # pylint: disable=attribute-defined-outside-init
                extension.package_name
            )
            extension_dir = self.get_extension_build_directory(extension.name)
            extension_suffix = (
                self.extension_suffix  # sysconfig.get_config_var("EXT_SUFFIX")
            )

            # Should I also allow this to be overridable in extension?
            config = "Debug" if self.debug else "Release"
            cmake_args = [
                f"-DCMAKE_BUILD_TYPE={config}",
                f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{config}={extension_dir}",
                # Needed for windows (more specifically .dll platforms).
                # It is safe to leave for all systems although will erroneously
                # add any .exe's created, which shouldn't exist anyway
                #
                # May remove for .so systems but without further testing it is
                # an unnecessary risk to remove
                f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{config}={extension_dir}",
                f"-DPYTHON_EXTENSION_SUFFIX={extension_suffix}",
            ]
            if extension.generator:
                cmake_args.append(f"-G {extension.generator}")

            if not self.build_temp_path.exists():
                self.build_temp_path.mkdir(parents=True)

            print(self.build_temp_path)
            print("WHat What", extension.cmake_lists_root_dir)
            # Config -> outputs in our temp dir
            subprocess.run(
                ["cmake", extension.cmake_lists_root_dir, *cmake_args],
                cwd=self.build_temp,
                check=True,
                #capture_output=True,
            )

            # Build -> builds the config (AKA generated solution/makefiles) in
            # our temp dir but outputs have already been setup in cmake_args
            # TODO: Update
            build_cmd = ["cmake", "--build", ".", "--config", config]
            if extension.targets is not None:
                build_cmd.append("--target")
                # TODO: Check if it requires args as a separate strings or
                # if Joint is okay
                build_cmd.append(" ".join(extension.targets))

            if self.parallel:
                build_cmd.append(f"-j {self.parallel}")
            else:
                build_cmd.append("-j")

            subprocess.run(build_cmd, cwd=self.build_temp, check=True)

    def get_extension_build_directory(self, extension_name):
        """This function gets the full path to the build directory as
        specified by "self.build_lib" or the source directory if
        inplace is set.

        """
        extension_path = self.get_ext_fullpath(extension_name)
        return pathlib.Path(extension_path).resolve().parent

    # I know I should have get_output_mapping but with cmake ....

    # override
    def get_outputs(self) -> List[str]:
        # From super implementation:
        """Sanity check the 'extensions' list -- can't assume this is being
        done in the same run as a 'build_extensions()' call (in fact, we can
        probably assume that it *isn't*!).
        """

        self.check_extensions_list(self.extensions)
        # I guess but should probably check
        # shouldnt this also return the outputs (dll's and pyd's etc)
        return self.extensions  # I think this part is wrong but...

    # override
    def check_extensions_list(self, extensions):
        """Ensures that the list of extensions provided by setuptools.setup's
        ext_modules parameter is valid. i.e. it is a list of
        CeMakeExtension objects. Old style list of 2-tuples is no longer supported.

        Raise Setuptools' SetupError if invalid extension found
        """
        if not isinstance(extensions, list):
            raise errors.SetupError(
                "'ext_modules' argument must be a list of CeMakeExtension instances "
                f"however ext_modules had type {type(extensions)}"
            )

        if not all(isinstance(ext, CeMakeExtension) for ext in extensions):
            raise errors.SetupError(
                "Each element of 'ext_modules' must be an instance of "
                "the CeMakeExtension class"
            )
