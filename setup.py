from setuptools import setup

setup(name='beer_road',
    version='1.0',
    description='Collecting beers along the path in Germany',
    url='https://github.com/itfrosts/Beer_Road',
    author='itfrosts',
    packages=['beer_road'],
    install_requires=[
        'argparse',
        'pandas'
    ]

)