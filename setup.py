from ossaudiodev import openmixer
from setuptools import setup, find_packages

setup(
    name="srtTranslator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        openai,
        re,
        sys,
        os,
        time,
        requests,
        keyboard,
        threading
    ],
)