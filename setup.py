from pathlib import Path

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = {file.stem: file.read_text().splitlines() for file in Path(".").glob("requirements/*.txt")}

setup(
    name="pam",
    version="0.2.4",
    author="Fred Shone",
    author_email="",
    description="Pandemic Activity Modeller/Modifier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arup-group/pam",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": ["pam = pam.cli:cli"], 
        'mkdocs.plugins': ['generate-api = mkdocs_plugins.api_generator:AddAPIPlugin']
    },
    extras_require={
        "docs": requirements["docs"],
        "dev": requirements["docs"] + requirements["dev"],
    },
    install_requires=requirements["base"],
)
