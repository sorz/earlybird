#!/usr/bin/env python3
from setuptools import setup


setup(
    name='earlybird',
    version='0.1.0',
    author='Shell Chen',
    author_email='me@sorz.org',
    packages=['earlybird'],
    entry_points="""
    [console_scripts]
    earlybird = earlybird:run
    """,
    install_requires=[
        'jinja2',
        'pyroute2',
    ],
)

