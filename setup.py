import setuptools

about = {}
with open("myst_literate/__about__.py") as f:
    exec(f.read(), about)

with open("README.md", "r") as f:
    long_description = f.read()
description = long_description.splitlines()[1].strip("> ")

setuptools.setup(
    name="myst-literate",
    version=about["__version__"],
    author="Matthew Edwards",
    author_email="mje-nz@users.noreply.github.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mje-nz/myst-literate",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
