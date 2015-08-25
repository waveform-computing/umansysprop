.. _quickstart:

===========
Quick Start
===========

It is strongly recommended that you use UManSysProp from within the `IPython`_
shell. The API is designed with documentation built-in which can be queried
"live" from within the environment, and this is considerably easier from within
the IPython shell. The rest of this guide will include tips for usage within
IPython, but examples will be given in the syntax of the regular Python shell.

The first step in using the UManSysProp system is creating a
:class:`~umansysprop.client.UManSysProp` instance. This requires the URL of the
UManSysProp server which defaults to
``http://umansysprop.seaes.manchester.ac.uk/``::

    >>> import umansysprop.client
    >>> client = umansysprop.client.UManSysProp()

Once you have a client instance, you can query it to find out what methods are
available from the web API. Within the IPython shell this can be done simply by
entering ``client.`` and pressing the Tab key twice. Alternatively, the
following one-liner in the regular Python shell can be used to query
non-private methods::

    >>> [m for m in dir(client) if not m.startswith('_')]
    ['CCN_potential_inorg',
     'CCN_potential_inorg_org',
     'CCN_potential_org',
     'absorptive_partitioning',
     'absorptive_partitioning_no_ions',
     'activity_coefficient_inorg_org',
     'activity_coefficient_org',
     'critical_property',
     'hygroscopic_growth_factor_inorg',
     'hygroscopic_growth_factor_inorg_org',
     'hygroscopic_growth_factor_org',
     'sub_cooled_density',
     'vapour_pressure']

Once you've selected a method to call you can discover what parameters it takes
and what it expects in those parameters by querying the method's documentation.
Within the IPython shell this can be viewed simply by appending ``?`` to the
method name. Alternatively, the :func:`help` function can be used in a regular
Python shell::

    >>> help(client.vapour_pressure)
    Help on method vapour_pressure in module umansysprop.client:

    vapour_pressure(self, compounds, temperatures, vp_method, bp_method)...
        Calculates vapour pressures for all specified *compounds* (given as a
        sequence of SMILES strings) at all given *temperatures* (a sequence of
        floating point values giving temperatures in degrees Kelvin). The
        *vp_method* parameter is one of the strings:

        * 'nannoolal'
        * 'myrdal_and_yalkowsky'
        * 'evaporation'
        ...

The various methods are not included within this documentation (which only
covers the framework) simply because they are defined by the server API (not by
this package). The documentation for each tool can viewed on the UManSysProp
`API documentation page`_.

Calling any of the methods will (in the event of success) return a
:class:`~umansysprop.results.Result` instance. This is simply a :func:`list`
which contains a sequence of :class:`~umansysprop.results.Table` instances.
Each table has a name and this can be used to access the table in the owning
:class:`~umansysprop.results.Result` list. For example::

    >>> result = client.vapour_pressure(
    ... ['CCCC', 'C(CC(=O)O)C(=O)O', 'C(=O)(C(=O)O)O',
    ... 'CCCCC/C=C/C/C=C/CC/C=C/CCCC(=O)O'],
    ... [298.15, 299.15, 300.15, 310.15],
    ... vp_method='nannoolal', bp_method='nannoolal')
    >>> result
    [<Table name="pressures">]
    >>> result.pressures
    <Table name="pressures">

:class:`~umansysprop.results.Table` instances have a friendly string
representation which can be used at the command line for quick evaluation of
the contents::

    >>> print(result.pressures)
           |           CCCC | C(CC(=O)O)C(=O)O | C(=O)(C(=O)O)O | CCCCC/C=C/C/C=C/CC/C=C/CCCC(=O)O
    -------+----------------+------------------+----------------+---------------------------------
    298.15 | 0.220914923012 |   -6.33293991048 | -5.19636054531 |                   -9.66033139516
    299.15 | 0.235479319348 |   -6.28117761855 | -5.15170377256 |                   -9.58901500825
    300.15 | 0.249933657549 |   -6.22986499517 | -5.10742877511 |                   -9.51835276669
    310.15 | 0.388688301563 |   -5.74023509659 | -4.68464352888 |                   -8.84581513627

The :class:`~umansysprop.results.Table` class also provides several attributes
which can be used to access the data in a variety of common extension formats,
specifically numpy `ndarrays`_ and pandas `DataFrames`_::

    >>> result.pressures.as_dataframe
    Compound         CCCC  C(CC(=O)O)C(=O)O  C(=O)(C(=O)O)O  \
    Temperature
    298.15       0.220915         -6.332940       -5.196361
    299.15       0.235479         -6.281178       -5.151704
    300.15       0.249934         -6.229865       -5.107429
    310.15       0.388688         -5.740235       -4.684644

    Compound     CCCCC/C=C/C/C=C/CC/C=C/CCCC(=O)O
    Temperature
    298.15                              -9.660331
    299.15                              -9.589015
    300.15                              -9.518353
    310.15                              -8.845815

.. _IPython: http://ipython.org/
.. _API documentation page: http://vm-woody009.itservices.manchester.ac.uk/api
.. _ndarrays: http://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html
.. _DataFrames: http://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe

