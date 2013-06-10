from setuptools import setup, find_packages
from reprozip.utils import VERSION

setup(
      name = 'reprozip',
      version = VERSION,
      author = 'Fernando Chirigati',
      author_email = 'fchirigati@nyu.edu',
      packages = find_packages(),
      license = 'LICENSE.txt',
      include_package_data = True,
      description = 'Reproducibility tool for packing and unpacking experiments.',
      long_description = open('README.txt').read(),
      install_requires = [
                          'pymongo >= 2.5.2'
                          ],
      classifiers = [
                     'Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'Intended Audience :: End Users/Desktop',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: Unix',
                     'Topic :: Utilities'
                     ]
)