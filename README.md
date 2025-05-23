# Premcloud Common Packages
This Repository contains packages with common logic across models

# Getting Started
Folders inside packages

### Detectaicore
Contains Data Models and constants for PII Classification Model, Logging and Exception Behaviours class shared by all models

### ov_helpers
Contains OpenVino classes to convert models to IR OpenVino format and to load and do Inference with OpenVino Runtime. We have conversion scripts for Microsoft Florence 2 AND Microsoft Phi3 Vision Instruct

# Build and Test
- Go to the folder and execute python setup.py sdist bdist_wheel
- in the same folder run twine upload dist/*

```
PACKAGES

pip install -e . (from detectaicore to install the package locally and be able to edit)
pip library


https://www.freecodecamp.org/news/build-your-first-python-package/

python setup.py sdist bdist_wheel
twine upload dist/*

pip install -U detectaicore --force
```
# Contribute

These two python packages are in pypi under my account olonok . To push new releases you need a token , which i will need to provide. Contact me to olonok@gmail.com and agree the process. ALso you can continue with the development and changes in local

![alt text](image.png)

