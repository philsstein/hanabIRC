from distutils.core import setup
from setuptools import find_packages

setup(
    name='HanabIRC',
    version='0.1',
    packages=find_packages(exclude=['test']), 
    license='FreeBSD License', 
    author='Geoff Lawler', 
    author_email='geoff.lawler@gmail.com',
    description='An IRC bot that organizes and plays the card game Hanabi.',
    long_description=open('README.txt').read(),
    url='https://github.com/philsstein/hanabIRC',
)
