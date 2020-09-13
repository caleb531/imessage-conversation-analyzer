#!/usr/bin/env python3

from setuptools import setup


# Get long description (used on PyPI project page)
def get_long_description():
    with open('README.md', 'r') as readme_file:
        return readme_file.read()


setup(
    name='imessage-conversation-analyzer',
    version='0.1.0',
    description='Analyzes the entire history of a macOS Messages conversation',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/caleb531/imessage-conversation-analyzer',
    author='Caleb Evans',
    author_email='caleb@calebevans.me',
    license='MIT',
    keywords='apple imessage macos conversation chat analysis pandas',
    packages=['ica'],
    install_requires=['pandas', 'tabulate'],
    entry_points={
        'console_scripts': [
            'ica=ica.__main__:main'
        ]
    }
)
