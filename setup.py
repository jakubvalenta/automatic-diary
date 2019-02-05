from pathlib import Path

from setuptools import find_packages, setup

setup(
    name='automatic-journal',
    version='0.1.0',
    description='Automatic journal',
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    url='https://lab.saloun.cz/jakub/automatic-journal',
    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',
    license='GNU General Public License v3 (GPLv3)',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': ['automatic-journal=automatic_journal.cli:main']
    },
)
