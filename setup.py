from setuptools import setup

setup(
    name='eauctions CLI',
    version='0.1.0',
    py_modules=['eauctions'],
    install_requires=[
        'Click',
        'requests',
        'beautifulsoup4',
        'lxml',
        'html5lib',
        'pandas',
        'urllib3',
        'price-parser',
        'selenium'
    ],
    entry_points='''
        [console_scripts]
        eauctions=eauctions:cli
    ''',
)
