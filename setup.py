import os
import importlib
from PyQt5 import uic

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

package = 'comet_longterm'
package_dir = os.path.join(os.path.dirname(__file__), package)

version = importlib.import_module(package, os.path.join(package_dir, '__init__.py')).__version__

class BuildPyCommand(build_py):
    def run(self):
        uic.compileUiDir(os.path.join(package_dir, 'ui'))
        build_py.run(self)

setup(
    name='comet-longterm',
    version=version,
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    packages=find_packages(),
    install_requires=[
        'comet>=0.1',
    ],
    dependency_links=[
        'git+https://github.com/hephy-dd/comet.git@master',
    ],
    entry_points={
        'gui_scripts': [
            'comet-longterm = comet_longterm.main:main',
        ],
    },
    cmdclass={
        'build_py': BuildPyCommand,
    },
    license="GPLv3",
)
