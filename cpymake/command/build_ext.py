"""
cpymake's build_ext command for building a python C/C++ extension using CMake
"""

import os
import subprocess
import sysconfig

from typing import List

from setuptools import errors

# VV Whilst a build_ext it's different enough to just extend from Command
# (although distutils' original is way better)
# NOTE: May wish to revert for other os' like darwin (mac?)
# from setuptools.command.build_ext import build_ext
from setuptools import Command
from setuptools.command.build import SubCommand
from cpymake.extension import Extension

# NOTE: By not inheriting from setuptools' build_ext (as we'd rather extend distutil's)
# we have to reimplement a lot of methods but it (could) be worth it


# Sub Command is a Protocol but we want to explicitly inherit
class build_ext(Command, SubCommand):  # pylint: disable=too-many-instance-attributes
    """CPyMake's build_ext class that can be used as a plugin for setuptools
    to build extension modules that use CMake as their build (generator) system
    """

    description = "build C/C++ extensions using CMake (compile/link to build directory)"

    user_options = [
        ("build-lib=", "b", "directory for compiled extension modules"),
        ("build-temp=", "t", "directory for temporary files (build by-products)"),
        # VV not supported yet but we will leave it for now (-A in CMAKE)
        (
            "plat-name=",
            "p",
            (
                "platform name to cross-compile for, if supported "
                f"(default: {sysconfig.get_platform()})"
            ),
        ),
        (
            "inplace",
            "i",
            (
                "ignore build-lib and put compiled extensions into the source "
                "directory alongside your pure Python modules"
            ),
        ),
        ("define=", "D", "C preprocessor macros to define"),
        ("undef=", "U", "C preprocessor macros to undefine"),
        ("debug", "g", "compile/link with debugging information"),
        ("force", "f", "forcibly build everything (ignore file timestamps)"),
        ("parallel=", "j", "number of parallel build jobs"),
    ]

    boolean_options = ["inplace", "debug", "force"]

    # TODO: VV Show generators and possibly platforms?
    # help_options = [
    #     ("help-compiler", None, "list available compilers", show_compilers),
    # ]

    # override
    def initialize_options(self):
        # pylint: disable=attribute-defined-outside-init
        print("***** Initialize_options Called!")

        self.package = None
        self.extensions = None

        self.build_lib = None
        self.build_temp = None
        self.plat_name = None
        self.inplace = 0
        self.editable_mode = False

        self.define = None
        self.undef = None
        self.debug = None
        self.force = None
        self.parallel = None

    # override
    def finalize_options(self):
        # pylint: disable=attribute-defined-outside-init

        print("***** Finalize_options Called")

        self.set_undefined_options(
            "build",
            ("build_lib", "build_lib"),
            ("build_temp", "build_temp"),
            ("debug", "debug"),
            ("force", "force"),
            ("parallel", "parallel"),
            ("plat_name", "plat_name"),
        )

        if self.package is None:
            self.package = self.distribution.ext_package  # <- what is this !!?

        self.extensions = self.distribution.ext_modules or []

        if os.name == "nt":
            if self.debug:
                self.build_temp = os.path.join(self.build_temp, "Debug")
            else:
                self.build_temp = os.path.join(self.build_temp, "Release")

        # TODO:
        # defines and undefs

        # NOTE: May want to do it more like how numpy does
        # (i.e convert to int regardless)
        if isinstance(self.parallel, str):
            try:
                self.parallel = int(self.parallel)
            except ValueError as e:
                raise errors.OptionError("--parallel/-j should be an integer") from e

        # TODO: custom check extension list

        # TODO: Do we need??
        # for ext in self.extensions:
        #     ext._full_name = self.get_ext_fullname(ext.name)
        #     # this is split into two loops in setuptools but why?
        #     self.ext_map[

        if self.editable_mode:
            self.inplace = True

    # Don't call super as we need all custom behaviour
    # override
    def run(self):
        print("***** Run Called")

        print(
            "***** cpymake's build_ext's variables =",
            f"package = {self.package}",
            "extensions = printed_later",
            f"build_lib = {self.build_lib}",
            f"build_temp = {self.build_temp}",
            f"plat_name = {self.plat_name}",
            f"inplace = {self.inplace}",
            f"editable_mode = {self.editable_mode}",
            f"define = {self.define}",
            f"undef = {self.undef}",
            f"debug = {self.debug}",
            f"force = {self.force}",
            f"parallel = {self.parallel}",
            sep="\n\t",
        )

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
        print("****** Build_extensions Called")

        # origional_package = self.package

        # Really useful to see what additional options we can use
        # print('***', *(self.user_options), sep="\n")
        # Same as python setup.py build_ext --help

        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)

        print("***** print each ext:")

        for extension in self.extensions:
            print("******", extension)
            # Looks dodgy but it's been years since I made this so...
            # Actually maybe not...
            # self.package = (  # pylint: disable=attribute-defined-outside-init
            #     extension.package_name
            # )
            # extension_dir = self.get_extension_build_directory(extension.name)
            # extension_dir = os.path.abspath(
            #     os.path.dirname(self.get_ext_fullpath(extension.name))
            # )
            # extension_path = "apep" #os.path.dirname(self.get_ext_fullpath(extension.name))
            extension_path = os.path.dirname(self.get_ext_fullpath(extension.name))
            extension_base = os.getcwd() #os.path.abspath(self.build_lib)

            # print("extension_dir:", extension_path)#dir)
            print("extension_path:", extension_path)#dir)
            print("extension_base:", extension_base)#dir)
            print("cwd:", os.getcwd())
            extension_suffix = (
                # self.extension_suffix  # sysconfig.get_config_var("EXT_SUFFIX")
                sysconfig.get_config_var("EXT_SUFFIX")
            )
            print("extension fullname =", self.get_ext_fullname(extension.name))
            print("extension filename =", self.get_ext_filename(extension.name))
            print("extension fullpath =", self.get_ext_fullpath(extension.name))

            # Should I also allow this to be overridable in extension?
            config = "Debug" if self.debug else "Release"
            cmake_args = [
                f"-DCMAKE_BUILD_TYPE={config}",
                # f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{config}={extension_dir}",
                f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extension_path}",
                # Needed for windows (more specifically .dll platforms).
                # It is safe to leave for all systems although will erroneously
                # add any .exe's created, which shouldn't exist anyway
                #
                # May remove for .so systems but without further testing it is
                # an unnecessary risk to remove
                # f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{config}={extension_dir}",
                (
                    "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY="
                    f"$<PATH:ABSOLUTE_PATH,{extension_path},{extension_base}>"
                ),
                # f"-DPYTHON_EXTENSION_SUFFIX={extension_suffix}",
                f"-DPYTHON_EXTENSION={extension_suffix}",
                #NOTE: VV Doesn't work on windows for some reason (being overwritten)
                # f"-DCMAKE_SHARED_LIBRARY_SUFFIX={extension_suffix}",
            ]
            if extension.generator:
                cmake_args.append(f"-G {extension.generator}")

            # Config -> outputs in our temp dir
            print(
                "----- Configure:\n",
                subprocess.run(
                    ["cmake", extension.cmake_lists_root_dir, *cmake_args],
                    # cwd=self.build_temp,
                    # check=True,
                    capture_output=True,
                ),
            )

            print("~~~~~~~ CWD=", os.getcwd())

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

            print("##### pre-run")
            print(
                "----- Configure:\n",
                subprocess.run(
                    build_cmd,
                    # check=True
                ),  # cwd=self.build_temp,
            )
            print("##### post-run")

    # TODO: These three functions need a rewrite! I think we can use special cmake
    # runs, unfortunatly I'm not 100% sure plus it may well
    # be considered "a side affect" although not really? but i guess configure is
    # required

    # NOTE: Possibly too different from original but.... I mean this whole thing
    # could be a separate command caled build_cmake_ext for example

    # override
    def get_output_mapping(self) -> dict[str, str]:
        print("***** Get_output_mapping Called")

        # They sort an interator and convert to dict but lets just make it here

        # might be neater to just use if rather than if not
        if not self.inplace:
            return {}

        output_mapping = {}

        for ext in self.extensions:
            inplace_file, regular_file = self.get_ext_paths(ext.name)
            output_mapping[regular_file] = inplace_file

        return output_mapping

    # override
    def get_outputs(self) -> list[str]:
        print("****** Get_outputs Called")

        # NOTE: Ideally we would also get clibs that the CMake extension requires/builds
        # unfortunatly I dont yet see how so for now.....
        # Can cmake tell us ??? I think so, so... what happens then can we use
        # vars set in run? will run have been "run" first?

        if self.inplace:
            return list(self.get_output_mapping().keys())

        self.check_extensions_list(self.extensions)
        outputs = []
        for ext in self.extensions:
            outputs.append(self.get_ext_fullpath(ext.name))
        print("***** Outputs =", outputs)

        return outputs

    # override
    def get_source_files(self):
        print("***** Get_source_files Called")

        self.check_extensions_list(self.extensions)
        # TODO: For now this is all we can do
        filenames = []
        for ext in self.extensions:
            filenames.append(ext.cmake_lists_root_dir)
        return filenames  # contains path for now so change probably

    # override
    def check_extensions_list(self, extensions):
        """Ensures that the list of extensions provided by setuptools.setup's
        ext_modules parameter is valid. i.e. it is a list of
        CeMakeExtension objects. Old style list of 2-tuples is no longer supported.

        Raise Setuptools' SetupError if invalid extension found
        """

        print("***** Check_extensions_list Called")

        if not isinstance(extensions, list):
            raise errors.SetupError(
                "'ext_modules' argument must be a list of cpymake's "
                "Extension instances "
                f"however ext_modules had type {type(extensions)}"
            )

        if not all(isinstance(ext, Extension) for ext in extensions):
            raise errors.SetupError(
                "Each element of 'ext_modules' must be an instance of "
                "the cpymake's Extension class"
            )

    # -- Name generators -----------------------------------------------
    def get_ext_fullname(self, ext_name: str) -> str:
        """Adds the `package.` prefix"""
        if self.package is None:
            return ext_name

        return self.package + "." + ext_name

    def get_ext_filename(self, ext_name: str) -> str:
        """Converts the name of an extension (eg. "foo.bar") into the name
        of the file from which it will be loaded (eg. "foo/bar.so", or
        "foo\bar.pyd").
        """

        ext_path = ext_name.split(".")
        ext_suffix = os.getenv("CPYMAKE_EXT_SUFFIX") or sysconfig.get_config_var(
            "EXT_SUFFIX"
        )

        return os.path.join(*ext_path) + ext_suffix

    def get_ext_paths(self, ext_name) -> tuple[str, str]:
        fullname = self.get_ext_fullname(ext_name)
        modpath = fullname.split(".")

        # TODO: Check for bugs as original code only used last elem of modpath
        filename = self.get_ext_filename(fullname)
        package = ".".join(modpath[:-1])

        build_py = self.get_finalized_command("build_py")
        package_dir = build_py.get_package_dir(package)  # type: ignore

        # NOTE: os.path.basename required with this version. Depends on whether
        # os.path.join (with multiple args) has greater complexity than
        # os.path.basename (depends on whether concat is more complex than
        # iteration (depending on C implementation))
        inplace_file = os.path.join(package_dir, os.path.basename(filename))
        regular_file = os.path.join(self.build_lib, filename)
        return (inplace_file, regular_file)

    def get_ext_fullpath(self, ext_name: str) -> str:
        """Returns the path of the filename for a given extension.

        The file is located in `build_lib` or directly in the package
        (inplace option).
        """
        inplace_path, regular_path = self.get_ext_paths(ext_name)

        if not self.inplace:
            # returning: build_dir/package/path/filename
            return regular_path

        # returning: package_dir/filename
        return os.path.abspath(inplace_path)
