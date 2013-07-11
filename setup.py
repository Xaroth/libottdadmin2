from distutils.core import setup

setup(
    name='libottdadmin2',
    version='0.0.1',
    author="Steven 'Xaroth' Noorbergen",
    author_email='xaroth@opendune.org',
    packages=['libottdadmin2'],
    scripts=['bin/openttd-admin-rcon.py', 'bin/openttd-admin-test-json.py'],
    url='https://github.com/xaroth/libottdadmin2',
    license='http://creativecommons.org/licenses/by-nc-sa/3.0/',
    description='A small library for the Admin Port interface for OpenTTD.',
    long_description=open('README.md').read(),
    install_requires=[
    ],
)