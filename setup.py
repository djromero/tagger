from distutils.core import setup

setup(name='Tagger',
      version='20110709',
      description='A module for extracting relevant tags from text documents.',
      author='Alessandro Presta',
      author_email='alessandro.presta@gmail.com',
      url='https://github.com/apresta/tagger',
      packages=['tagger'],
      package_dir={'tagger': '.'},
      package_data={'tagger': ['data/*.pkl']},
      requires=['nltk (>=3.0.1)'],
      provides=['tagger'])
