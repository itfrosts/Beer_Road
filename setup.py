from setuptools import setup

setup(name='Beer_Road',
    version='1.0',
    description='Collecting beers along the path in Germany',
    url='https://github.com/itfrosts/Beer_Road',
    author='itfrosts',
    packages=['Beer_Road'],
    install_requires=[
        'argparse',
        'pandas'
    ]
)