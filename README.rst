===================================
saitama: pure postgres unit-testing
===================================

.. image:: https://github.com/spapanik/saitama/actions/workflows/tests.yml/badge.svg
  :alt: Tests
  :target: https://github.com/spapanik/saitama/actions/workflows/tests.yml
.. image:: https://img.shields.io/github/license/spapanik/saitama
  :alt: License
  :target: https://github.com/spapanik/saitama/blob/main/LICENSE.txt
.. image:: https://img.shields.io/pypi/v/saitama
  :alt: PyPI
  :target: https://pypi.org/project/saitama
.. image:: https://pepy.tech/badge/saitama
  :alt: Downloads
  :target: https://pepy.tech/project/saitama
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :alt: code style: black
  :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/build%20automation-yamk-success
  :alt: build automation: yam
  :target: https://github.com/spapanik/yamk
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
  :alt: Lint: ruff
  :target: https://github.com/charliermarsh/ruff

``saitama`` is offering a way to write unittest and migrations in pure postgres.

In a nutshell
-------------

Installation
^^^^^^^^^^^^

The easiest way is to use pip to install saitama.

.. code:: console

    $ pip install --user saitama

Usage
^^^^^

``saitama``, once installed, offers a single command, ``punch``, that controls the migrations and the testing.
``punch`` follows the GNU recommendations for command line interfaces, and offers:

* ``-h`` or ``--help`` to print help, and
* ``-V`` or ``--version`` to print the version


Links
-----

- `Documentation`_
- `Changelog`_


.. _poetry: https://python-poetry.org/
.. _Changelog: https://github.com/spapanik/saitama/blob/main/CHANGELOG.rst
.. _Documentation: https://saitama.readthedocs.io/en/latest/
