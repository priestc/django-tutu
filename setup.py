# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="django-tutu",
    version='0.1.0',
    description='Performance graphs for django projects',
    #long_description=open('README.md').read(),
    author='Chris Priest',
    author_email='nbvfour@gmail.com',
    url='https://github.com/priestc/django-tutu',
    packages=find_packages(),
    #scripts=['bin/moneywagon'],
    include_package_data=True,
    license='LICENSE',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['django', 'psutil']
)
