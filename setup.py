from setuptools import setup, find_packages

setup(
    name='comet-longterm',
    version='0.1.1',
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'comet @ https://github.com/hephy-dd/comet/archive/master.zip#egg=comet-0.1.0',
    ],
    package_data={
        '': [
            '*.ui',
        ],
    },
    entry_points={
        'gui_scripts': [
            'comet-longterm = comet_longterm.__main__:main',
        ],
    },
    test_suite='tests',
    license="GPLv3",
)
