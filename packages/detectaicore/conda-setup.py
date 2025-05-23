from setuptools import setup, find_packages


import conda_build.bdist_conda

setup(
    name="detectaicore",
    version="1.0",
    distclass=conda_build.bdist_conda.CondaDistribution,
    conda_buildnum=1,
)
