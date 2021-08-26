import re
import sys
from setuptools import setup, find_packages

if sys.version_info[0] < 3:
    raise SystemExit("Error: blocksat-cli requires Python 3")
    sys.exit(1)

version = re.search(r'^__version__\s*=\s*"(.*)"',
                    open('blocksatcli/main.py').read(), re.M).group(1)

long_description = """# Blockstream Satellite CLI

A command-line interface for configuring, running and monitoring a Blockstream
Satellite receiver setup.

"""

setup(
    name="blocksat-cli",
    packages=find_packages(),
    entry_points={"console_scripts": ['blocksat-cli = blocksatcli.main:main']},
    version=version,
    description="Blockstream Satellite CLI",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Blockstream Corp",
    author_email="satellite@blockstream.com",
    url="https://github.com/Blockstream/satellite",
    install_requires=[
        'distro', 'requests', 'python-gnupg>=0.4.7', 'sseclient-py', 'qrcode',
        'zfec>=1.5.4', 'pysnmp'
    ],
    package_data={'blocksatcli': ['mib/*.mib', 'mib/*.txt', 'gpg/*.gpg']},
    classifiers=[
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    python_requires='>=3')
