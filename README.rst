===================================
saitama: pure postgres unit-testing
===================================

.. image:: https://github.com/spapanik/saitama/actions/workflows/test.yml/badge.svg
  :alt: Test
  :target: https://github.com/spapanik/saitama/actions/workflows/test.yml
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
  :alt: Code style
  :target: https://github.com/psf/black

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
