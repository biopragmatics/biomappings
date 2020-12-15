from os import path
from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as fh:
    long_description = fh.read()


setup(name='biomappings',
      version=version,
      description=('Curated and predicted mappings between biomedical '
                   'identifiers in different namespaces.'),
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/biomappings/biomappings',
      author='Biomappings developers',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3.8'
      ],
      packages=find_packages(),
      install_requires=['requests'],
      extras_require={'test': ['nose'},
      keywords=['biology']
      )
