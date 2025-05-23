import sys

from setuptools import find_packages, setup

from blocksatcli import __version__

if sys.version_info[0] < 3:
    raise SystemExit("Error: blocksat requires Python 3")
    sys.exit(1)

long_description = """# Blockstream Satellite Interface

A graphical and command-line interface for configuring, running and monitoring
a Blockstream Satellite receiver setup.

"""

dependencies = [
    'distro',
    'packaging',
    'pysnmplib',
    'python-gnupg>=0.4.7',
    'qrcode',
    'requests',
]

if sys.version_info >= (3, 13):
    # Version 6.7.3 is not available for Python 3.13
    dependencies.append('pyside6>=6.8.1')
else:
    dependencies.append('pyside6==6.7.3')

# FIXME: Remove this once a pysnmp version supporting Py3.12 becomes available
if sys.version_info >= (3, 12):
    dependencies.append('pyasyncore==1.0.2')

setup(name="blocksat",
      packages=find_packages(),
      entry_points={
          "console_scripts": [
              'blocksat-cli = blocksatcli.main:main',
              'blocksat-gui = blocksatgui.main:main',
              'blocksatd = blocksatgui.blocksatd:main'
          ]
      },
      version=__version__,
      description="Blockstream Satellite Interface",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Blockstream Corp",
      author_email="satellite@blockstream.com",
      url="https://github.com/Blockstream/satellite",
      install_requires=dependencies,
      extras_require={
          "fec": ['zfec>=1.5.4'],
          "daemon": ['dbus-python']
      },
      package_data={
          'blocksatcli': ['mib/*.mib', 'mib/*.txt', 'gpg/*.gpg'],
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
          "Programming Language :: Python :: 3.9",
          "Programming Language :: Python :: 3.10",
          "Programming Language :: Python :: 3.11",
          "Programming Language :: Python :: 3.12",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
      ],
      python_requires='>=3.9')
