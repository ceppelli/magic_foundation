import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="magic_foundation",
    version="0.1.0",
    author="Luca Ceppelli",
    author_email="luca@ceppelli.com",
    description="Minimalistic library that simplifies the adoption of async/await (asyncio) programming style in a multithreaded application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ceppelli/magic_foundation",
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 5 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD 3-Clause License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires='>=3.7',
)