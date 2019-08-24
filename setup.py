import setuptools


def requirements():
    """Build the requirements list for this project"""
    requirements_list = []

    with open('requirements.txt') as requirements:
        for install in requirements:
            requirements_list.append(install.strip())

    return requirements_list


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="telegramreminder",
    version="0.0.2",
    description="telegram reminder bot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements(),
    url="https://github.com/BrandesDenis/telegramreminder",
    packages=setuptools.find_packages(),
    package_data={'telegramreminder': ['translations.ini']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)