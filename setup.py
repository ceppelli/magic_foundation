import setuptools
import codecs
import os.path

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError('Unable to find version string.')

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='magic_foundation',
    version=get_version('src/magic_foundation/__init__.py'),
    author='Luca Ceppelli',
    author_email='luca@ceppelli.com',
    description='Minimalistic library that simplifies the adoption of async/await (asyncio) programming style in a multithreaded application.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ceppelli/magic_foundation',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    license='BSD 3-clause "New" or "Revised License"',      
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Framework :: AsyncIO',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'CI: travis': 'https://travis-ci.com/github/ceppelli/magic_foundation',
        'Coverage: codecov': 'https://codecov.io/github/ceppelli/magic_foundation',
        'GitHub: issues': 'https://github.com/ceppelli/magic_foundation/issues',
        'GitHub: repo': 'https://github.com/ceppelli/magic_foundation',
    },
    python_requires='>=3.7',
)