from setuptools import setup, find_packages


VERSION = "0.0.3"
DESCRIPTION = "OpenVino Helpers"
LONG_DESCRIPTION = "Contains Scripts from OpenVIno to Convert and use LLMs"

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="ov_helpers",
    version=VERSION,
    author="Juan Huertas",
    author_email="olonok@hotmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license="MIT",
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
