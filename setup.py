import os

from setuptools import setup, find_packages

import socketIO


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()


setup(
    name='socketIO-client',
    version=socketIO.__version__,
    description='Barebones socket.io client library',
    long_description='\n\n'.join([README, CHANGES]),
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='socket.io node.js',
    author='Roy Hyunjin Han',
    author_email='starsareblueandfaraway@gmail.com',
    url='https://github.com/invisibleroads/socketIO-client',
    install_requires=[
        'anyjson',
        'websocket-client',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True)
