import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="telegramreminder",
    version="0.0.1",
    description="telegram reminder bot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BrandesDenis/telegramreminder",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)