import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('blocksatcli/main.py').read(),
    re.M
).group(1)


setup(
    name = "blocksat-cli",
    packages = ["blocksatcli"],
    entry_points = {
        "console_scripts": ['blocksat-cli = blocksatcli.main:main']
    },
    version = version,
    description = "Blockstream Satellite CLI",
    author = "Blockstream Corp",
    author_email = "satellite@blockstream.com",
    url = "https://github.com/Blockstream/satellite",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
)
