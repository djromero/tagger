from distutils.core import setup

setup(name='Tagger',
      version='20110709',
      description='A module for extracting relevant tags from text documents.',
      author='Alessandro Presta',
      author_email='alessandro.presta@gmail.com',
      url='https://github.com/apresta/tagger',
      packages=['tagger'],
      package_dir={'tagger': '.'},
      requires=['stemming (>=1.0)', 'nltk (>=2.0)'],
      provides=['tagger'])
