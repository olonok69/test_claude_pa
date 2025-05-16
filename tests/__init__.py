import os

# only in local env
LOCAL_ENV = os.getenv("LOCAL_ENV")
if LOCAL_ENV != None:
    if int(LOCAL_ENV) == 1:
        from image.ocr.app import *
