import sys

from setuptools import find_packages, setup

from blocksatcli import __version__

if sys.version_info[0] < 3:
    raise SystemExit("Error: blocksat-cli requires Python 3")
    sys.exit(1)

long_description = """# Blockstream Satellite CLI

A command-line interface for configuring, running and monitoring a Blockstream
Satellite receiver setup.

"""

dependencies = [
    'distro',
    'packaging',
    'pysnmplib',
    'python-gnupg>=0.4.7',
    'qrcode',
    'requests',
]

# FIXME: Remove this once a pysnmp version supporting Py3.12 becomes available
if sys.version_info >= (3, 12):
    dependencies.append('pyasyncore==1.0.2')

setup(
    name="blocksat-cli",
    packages=find_packages(exclude=('blocksatgui', 'blocksatgui.*')),
    entry_points={"console_scripts": ['blocksat-cli = blocksatcli.main:main']},
    version=__version__,
    description="Blockstream Satellite CLI",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Blockstream Corp",
    author_email="satellite@blockstream.com",
    url="https://github.com/Blockstream/satellite",
    install_requires=dependencies,
    extras_require={"fec": ['zfec>=1.5.4']},
    package_data={'blocksatcli': ['mib/*.mib', 'mib/*.txt', 'gpg/*.gpg']},
    classifiers=[
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    python_requires='>=3')
