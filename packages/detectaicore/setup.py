from setuptools import setup, find_packages


VERSION = "0.0.29"
DESCRIPTION = "Detect-ai core package"
LONG_DESCRIPTION = "Contains common functionality for rest of packages"

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="detectaicore",
    version=VERSION,
    author="Juan Huertas",
    author_email="",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=["python", "core package"],
    classifiers=[
        "Intended Audience :: Other Audience",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
