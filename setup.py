from importlib.metadata import entry_points
from setuptools import setup, find_packages

setup(
    name="pil-functional-layout",
    version="0.0.1",
    description="Functional layouting use pillow",
    author="TkskKurumi",
    maintainer="TkskKurumi",
    maintainer_email="zafkielkurumi@gmail.com",
    packages=["pil_functional_layout"],
    install_requires=[
        "pillow"
    ]
)