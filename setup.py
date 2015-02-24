import sys

try:
    from setuptools import setup
except ImportError:
    print("Tagger now needs setuptools in order to build. Install it using"
            " your package manager (usually python-setuptools) or via pip (pip"
            " install setuptools).")
    sys.exit(1)

setup(name='Tagger',
      version='0.2',
      description='A module for extracting relevant tags from text documents.',
      author='Alessandro Presta',
      author_email='alessandro.presta@gmail.com',
      url='https://github.com/apresta/tagger',
      packages=['tagger'],
      package_dir={'tagger': '.'},
      package_data={'tagger': ['data/*.pkl']},
      install_requires=['nltk'],
      provides=['tagger'])
