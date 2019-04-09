try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup



setup(
    name='libottdadmin2',
    version='0.0.3a1',
    author="Steven 'Xaroth' Noorbergen",
    author_email='xaroth@opendune.org',
    packages=['libottdadmin2', 'libottdadmin2.packets', 'libottdadmin2.client'],
    url='https://github.com/xaroth/libottdadmin2',
    license='http://creativecommons.org/licenses/by-nc-sa/3.0/',
    description='A small library for the Admin Port interface for OpenTTD.',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Common Public License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ]
)
