import pathlib
from setuptools import setup

with open(pathlib.Path(__file__).parent / "README.md", encoding='utf-8') as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="photoslicer",
    version="1.0.0",
    description="Detect, straighten and save photos from a flatbed scanner source image",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/francescovannini/photoslicer",
    author="Francesco Vannini",
    author_email="vannini@gmail.com",
    license="GPLv3",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6"
    ],
    packages=["photoslicer"],
    include_package_data=True,
    install_requires=["Pillow", "shapely", "opencv-python", "numpy"],
    entry_points={
        "console_scripts": [
            "photoslicer=photoslicer.__main__:main"
        ]
    }
)