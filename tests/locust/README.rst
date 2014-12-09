**************************************
Performance Testing with Python Locust
**************************************

This document describes the basic Load Performance Testing done using Python Locust: http://locust.io/

Setup
#####

The Locust test script is not dependent on the API Tests, so it is not necessary to configure the environment to run the API Tests themselves.

In order to set it up::

    pip install -r load-requirements.txt

**Note**: You may have to install other requirements using your Linux distribution's software manager, like gcc and python-devel

Configuration
#############

The configuration of the test script is almost entirely managed by the file *config.cfg*

+--------------------+---------------------------------------------+--------------------------------------+
|deuce               |                                             |                                      |
+--------------------+---------------------------------------------+--------------------------------------+
|vaultname_size      |50                                           |Defines the length of the randomly    |
|                    |                                             |generated vault name                  |
+--------------------+---------------------------------------------+--------------------------------------+
|num_blocks          |100                                          |The number of blocks that             |
|                    |                                             |make up a single file                 |
+--------------------+---------------------------------------------+--------------------------------------+
|block_size          |30720                                        |The size in bytes for an              |
|                    |                                             |individual block                      |
+--------------------+---------------------------------------------+--------------------------------------+
|dedup_ratio         |60                                           |De-duplication ratio (0 - 100)        |
+--------------------+---------------------------------------------+--------------------------------------+
|locust              |                                             |                                      |
+--------------------+---------------------------------------------+--------------------------------------+
|min_pause           |10000                                        |Minimum pause between operations (ms) |
+--------------------+---------------------------------------------+--------------------------------------+
|max_pause           |10000                                        |Maximum pause between operations (ms) |
+--------------------+---------------------------------------------+--------------------------------------+
|authentication      |                                             |                                      |
+--------------------+---------------------------------------------+--------------------------------------+
|use_auth            |True                                         |Use Identity and get an Auth Token    |
+--------------------+---------------------------------------------+--------------------------------------+
|api_user            |{api user}                                   |API User                              |
+--------------------+---------------------------------------------+--------------------------------------+
|api_key             |{api key}                                    |API Key                               |
+--------------------+---------------------------------------------+--------------------------------------+
|base_url            |https://identity.api.rackspacecloud.com/v2.0 |Identity Url                          |
+--------------------+---------------------------------------------+--------------------------------------+

Running the script
##################

In order to run the script with the web UI::

    locust -f locust_test.py --host=<http://deuce url>

To run the script with multiple slaves::

    locust -f locust_test.py --host=<http://deuce url> --master
    locust -f locust_test.py --host=<http://deuce url> --slave --master-host=<ip address to the master>
    locust -f locust_test.py --host=<http://deuce url> --slave --master-host=<ip address to the master>
    locust -f locust_test.py --host=<http://deuce url> --slave --master-host=<ip address to the master>

To run the script with no Web UI (you cannot use slaves)::

    locust -f locust_test.py --host=<http://deuce url> --no-web --clients=200 --hatch-rate=1 --num-request=10000

Generating a report
###################

You can generate a graphical report using the scripts available in:
    http://killera.github.io/test/2013/12/23/using-matplotlib-to-analyse-locust-performance-test-results/
    https://github.com/killera/python-foo-bar/tree/master/scientific_computation_and_visualization/exercises

**Note:** You will have to modify the script locust_trend.py to point to the correct logfile
