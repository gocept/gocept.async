# Copyright (c) 2007-2009 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
from setuptools import setup, find_packages


def read(filename):
    path = os.path.join('src', 'gocept', 'async', filename)
    return file(path).read() + '\n\n'


name = "gocept.async"
version = '0.3.2'


setup(
    name = name,
    version = version,
    author = "gocept gmbh & co. kg",
    author_email = "developers@gocept.com",
    url = 'http://pypi.python.org/pypi/gocept.async',
    description = "Asynchronous function calls using lovely.remotetask",
    long_description = (
        open('README.txt').read() + "\n\n" +
        read('README.txt') +
        open('CHANGES.txt').read() + "\n\n"
    ),
    license = "ZPL 2.1",
    keywords = "zope3 async asynchronous function",
    classifiers = (
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: Zope3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "License :: OSI Approved",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development",
        ),
    zip_safe = False,
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['gocept'],
    install_requires = [
        'ZODB3',
        'decorator',
        'lovely.remotetask>=0.3',
        'rwproperty',
        'setuptools',
        'zope.authentication',
        'zope.app.testing',
        'zope.component',
        'zope.deferredimport',
        'zope.dottedname',
        'zope.security',
        'zope.site',
        'zope.testing',
    ],
    extras_require=dict(test=[
        'zope.app.appsetup',
        'zope.app.security',
        'zope.app.testing',
        'zope.container',
        'zope.location',
        'zope.publisher',
        'zope.traversing',
    ]),
)
