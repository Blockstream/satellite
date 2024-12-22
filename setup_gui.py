import sys

from setuptools import find_packages, setup

from blocksatgui import __version__

if sys.version_info[0] < 3:
    raise SystemExit("Error: blocksat requires Python 3")
    sys.exit(1)

long_description = """# Blockstream Satellite GUI

A graphical user interface for configuring, running and monitoring a
Blockstream Satellite receiver setup.

"""

setup(
    name="blocksat-gui",
    packages=find_packages(exclude=('blocksatcli', 'blocksatcli.*')),
    entry_points={
        "console_scripts": [
            'blocksat-gui = blocksatgui.main:main',
            'blocksatd = blocksatgui.blocksatd:main'
        ]
    },
    version=__version__,
    description="Blockstream Satellite GUI",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Blockstream Corp",
    author_email="satellite@blockstream.com",
    url="https://github.com/Blockstream/satellite",
    install_requires=[
        'blocksat-cli==' + __version__,  # matching version
        'pyside6==6.7.3',
        'typing_extensions>=4.12.2'
    ],
    extras_require={"daemon": ['dbus-python']},
    package_data={
        'blocksatgui': [
            'static/*.svg', 'static/*.qss', 'config/*.service',
            'config/*.policy', 'config/*.conf'
        ]
    },
    data_files=[('share/applications',
                 ['blocksatgui/config/blocksatgui.desktop']),
                ('share/icons', ['blocksatgui/static/blocksaticon.svg'])],
    classifiers=[
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    python_requires='>=3')
