from distutils.core import setup
from setuptools import find_packages
from hanabIRC import __version__

setup(
    name='HanabIRC',
    version=__version__,
    packages=find_packages(exclude=['*test']),
    license='FreeBSD License', 
    author='Phil S. Stein', 
    author_email='phil.s.stein@gmail.com',
    description='An IRC bot that organizes and plays the card game Hanabi.',
    long_description=open('README.txt').read(),
    url='https://github.com/philsstein/hanabIRC',
    install_requires=['irc', 'PyYAML'],
    scripts=['bin/hanabIRC']
)
