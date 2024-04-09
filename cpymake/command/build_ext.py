"""
cpymake's build_ext command for building a python C/C++ extension using CMake
"""

import os
import shutil
import subprocess
import sysconfig

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

# NOTE: From looking at distutils it looks like self.verbose could be dangerous to use
# so we will comment out when things are called and leave it to be uncommented
# if needed


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

    # TODO: pass cmake path as option
    # override
    def initialize_options(self):
        # print("***** Initialize_options Called!")

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
        # print("***** Finalize_options Called")

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

        # TODO: See if we should keep this.
        # if os.name == "nt":
        #     if self.debug:
        #         self.build_temp = os.path.join(self.build_temp, "Debug")
        #     else:
        #         self.build_temp = os.path.join(self.build_temp, "Release")

        # TODO:
        # defines and undefs

        if isinstance(self.parallel, str):
            try:
                self.parallel = int(self.parallel)
            except ValueError as e:
                raise errors.OptionError("--parallel/-j should be an integer") from e

        # TODO: custom check extension list

        if self.editable_mode:
            self.inplace = True

    # override
    def run(self):
        # print("***** Run Called")

        if not self.extensions:
            return

        # TODO: extract and check if safe elsewhere?!
        # Ensure that CMake is present and working.
        try:
            subprocess.run(["cmake", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError as cpe:
            raise RuntimeError(
                "Cannot find CMake executable:\n"
                f"\tstdout = {cpe.stdout}\n"
                f"\tstderr = {cpe.stderr}"
            ) from cpe

        # NOTE: potentially optimise VV
        os.makedirs(os.path.abspath(self.build_temp), exist_ok=True)

        # NOTE: Whilst there are alternatives to this switch it's not worthwile
        # The extra work in functions such as (including get_ext_paths) aren't worth
        # optimising (80/20 rule REMEMBER IT!)
        local_inplace, self.inplace = self.inplace, 0

        self.build_extensions()

        if local_inplace:
            for ext in self.extensions:
                inplace_file, regular_file = self.get_ext_paths(ext.name)

                # NOTE: regular file (on windows) is an abspath but inplace isn't
                # which is okay
                if os.path.exists(regular_file):
                    # NOTE: Is this best method (I'm not too keen on high-level utils)
                    # however it seems optimised.
                    # Alternitivly we could use cmake -E copy since we're already using
                    # cmake.
                    shutil.copy2(regular_file, inplace_file, follow_symlinks=False)
                else:
                    # NOTE: May need to change but for now I feel this is acceptable
                    raise errors.FileError(
                        f"File {regular_file} does not exist.\n"
                        f"list of files in {regular_file} directory is:\n"
                        f"\t{os.listdir(os.path.dirname(regular_file))}"
                    )

        self.inplace = local_inplace

    # override
    def build_extensions(self):
        self.check_extensions_list(self.extensions)

        for extension in self.extensions:
            extension_suffix = sysconfig.get_config_var("EXT_SUFFIX")

            # Should I also allow this to be overridable in extension?
            config = "Debug" if self.debug else "Release"

            cmake_args = [
                f"-DCMAKE_BUILD_TYPE={config}",
                f"-DPYTHON_EXTENSION_SUFFIX={extension_suffix}",
                # ^^ TODO: wish there was a better way!! plus VV doesn't work
                # NOTE: VV Doesn't work on windows for some reason (being overwritten)
                # f"-DCMAKE_SHARED_LIBRARY_SUFFIX={extension_suffix}",
            ]

            ext_output_path = (
                f"$<PATH:REMOVE_FILENAME,{self.get_ext_fullpath(extension.name)}>"
            )

            # Should I use config versions? I dont think so but ...
            if os.name == "nt":
                cmake_args.append(f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={ext_output_path}")
            else:
                cmake_args.append(f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={ext_output_path}")

            if extension.generator:
                cmake_args.append(f"-G {extension.generator}")

            try:
                subprocess.run(
                    [
                        "cmake",
                        os.path.abspath(extension.cmake_lists_root_dir),
                        *cmake_args,
                    ],
                    cwd=self.build_temp,
                    # cwd=os.path.abspath(self.build_temp),
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as cpe:
                raise RuntimeError(
                    "CMake Configure failed:\n"
                    f"\tstdout = {cpe.stdout}\n"
                    f"\tstderr = {cpe.stderr}"
                ) from cpe

            build_cmd = [
                "cmake",
                "--build",
                ".",
                "--config",
                config,
                "--target",
                extension.target,
            ]

            # if extension.targets is not None:
            #     build_cmd.append("--target")
            #     # TODO: Check if it requires args as a separate strings or
            #     # if Joint is okay
            #     build_cmd.append(" ".join(extension.targets))

            if self.parallel:
                build_cmd.append(f"-j {self.parallel}")
            else:
                build_cmd.append("-j")

            try:
                subprocess.run(
                    build_cmd,
                    cwd=self.build_temp,
                    # cwd=os.path.abspath(self.build_temp),
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError as cpe:
                raise RuntimeError(
                    "CMake Build failed:\n"
                    f"\tstdout = {cpe.stdout}\n"
                    f"\tstderr = {cpe.stderr}"
                ) from cpe

    # TODO: These three functions need a rewrite! I think we can use special cmake
    # runs, unfortunatly I'm not 100% sure plus it may well
    # be considered "a side affect" although not really? but i guess configure is
    # required

    # NOTE: Possibly too different from original but.... I mean this whole thing
    # could be a separate command caled build_cmake_ext for example

    # override
    def get_output_mapping(self) -> dict[str, str]:
        # print("***** Get_output_mapping Called")

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
        # print("****** Get_outputs Called")

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

        return outputs

    # override
    def get_source_files(self):
        # print("***** Get_source_files Called")

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

        # print("***** Check_extensions_list Called")

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
            # return regular_path
            return os.path.abspath(regular_path)
            # return regular_path

        # returning: package_dir/filename
        return os.path.abspath(inplace_path)
