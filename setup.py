from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="pam",
    version="0.0.1",
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
    python_requires='>=3.6',
    install_requires=install_requires,
)
