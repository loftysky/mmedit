from setuptools import setup, find_packages

setup(
    name='mmedit',
    version='0.1.dev0',
    description='Lofty Sky\'s general editorial tools.',
    url='http://github.com/loftysky/mmedit',
    
    packages=find_packages(exclude=['build*', 'tests*']),

    author='Lofty Sky Development Team',
    author_email='opensource@loftysky.com',

    license='BSD-3',
    
    entry_points={
        'console_scripts': '''

            mmedit-ingest = mmedit.footage.ingest:main
            mmedit-relink = mmedit.footage.relink:main

        ''',
    },

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
