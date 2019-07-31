import imp
from setuptools import setup, find_packages

version = imp.load_source('comet_longterm', 'comet_longterm/__init__.py').__version__

setup(
    name='comet-longterm',
    version=version,
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    packages=find_packages(),
    install_requires=[
        'comet',
        'comet-qt',
    ],
    dependency_links=[
        'git+https://github.com/hephy-dd/comet.git@master',
        'git+https://github.com/hephy-dd/comet-qt.git@master',
    ],
    entry_points={
        'gui_scripts': [
            'comet-longterm = comet_longterm.main:main',
        ],
    },
    license="GPLv3",
)
