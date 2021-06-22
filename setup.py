from setuptools import setup, find_packages

setup(
    name='comet-longterm',
    version='0.11.0',
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'PyQt5==5.15.*',
        'PyQtChart==5.15.*',
        'PyVISA==1.11.*',
        'PyVISA-py==0.5.*',
        'pint==0.17.*',
        'comet @ https://github.com/hephy-dd/comet/archive/0.5.0.zip#egg=comet-0.5.0',
    ],
    package_data={
        'comet_longterm': [
            '*.ui',
        ],
    },
    entry_points={
        'console_scripts': [
            'comet-longterm = comet_longterm.__main__:main',
        ],
    },
    test_suite='tests',
    license="GPLv3",
)
