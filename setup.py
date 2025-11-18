from setuptools import setup

deps = [
    "bs4",
    "kanirequests",
]

setup(
    name="yfjpscraper",
    version="0.5.0",
    description="yahoo finance japan parser",
    author="fx-kirin",
    author_email="fx.kirin@gmail.com",
    url='https://github.com/fx-kirin/yfjpscraper',
    packages=["yfjpscraper"],
    install_requires=deps
)
