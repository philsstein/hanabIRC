from distutils.core import setup

setup(
    name='HanabIRC',
    version='0.1',
    packages=['hanabIRC',],
    license='FreeBSD License', 
    author='Geoff Lawler', 
    author_email='geoff.lawler@gmail.com',
    description='An IRC bot that organizes and plays the card game Hanabi.',
    long_description=open('README').read(),
    url='https://github.com/philsstein/hanabIRC',
    packages=find_packages(exclude=['test*']), 
)
