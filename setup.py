from setuptools import setup, find_packages

setup(
    name="easytti",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "retry",
        "selenium",
    ],
    author="Aviv Illoz",
    author_email="avivilloz@gmail.com",
    description=(
        "Automates the process of generating and downloading images from "
        "Bing's image creation service using Selenium WebDriver."
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/avivilloz/easytti",
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
