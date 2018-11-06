import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='sharepoint',
    version='0.0.1',
    author='James Classen',
    author_email='jclassen@ĝᶆӓīł.ᴄṓᴟ', #fix unicode stuff to email
    description='A Python-based SharePoint interface',
    long_description='A Python-based SharePoint interface, geared toward NTLM/AD/LDAP authentication.',
    long_description_content_type='text/markdown',
    url='https://github.com/nessalc/python-sharepoint',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'requests',
        'requests_ntlm',
    ]
)
