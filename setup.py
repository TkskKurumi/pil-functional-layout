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
    package_data={'pil_functional_layout': ['*.otf',"./samples/bubble/*"]},
    include_package_data=True,
    install_requires=[
        "pillow"
    ]
)
