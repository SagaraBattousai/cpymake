from setuptools import setup

setup(
    entry_points={
        "distutils.commands": [
            "cemake = cemake.cemake_build_ext:cmake_build_ext",
        ],
    },
)
