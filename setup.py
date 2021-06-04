from pathlib import Path

from setuptools import find_packages, setup

from automatic_diary import __title__

setup(
    name='automatic-diary',
    version='0.3.0',
    description=__title__,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    url='https://github.com/jakubvalenta/automatic-diary',
    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',
    license='GNU General Public License v3 or later (GPLv3+)',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa: E501
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'caldav',
        'dateparser',
        'ics',
        'jinja2',
        'more-itertools',
        'pystache',
        'python-dateutil',
        'requests',
        'tzlocal',
    ],
    entry_points={
        'console_scripts': [
            'automatic-diary=automatic_diary.cli:main',
            'automatic-diary-visualize=automatic_diary.visualize:main',
        ]
    },
)
