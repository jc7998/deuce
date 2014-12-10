*********************
API Testing using ZAP
*********************

ZAP (https://code.google.com/p/zaproxy/) can be used to complement the API Tests by providing basic penetration/security testing of the API

Pre-requisites
--------------

#) ZAP (Zed Attack Proxy) must be configured and running. This can be done locally or on a remote server. ZAP requires Java

#) Setting up the Deuce API Tests. The ZAP test takes advantage of the Deuce API Tests (configuration, client code). Please follow the instructions to set up the Deuce API Tests

Configuration
-------------

The configuration file (zap/config.cfg) only has a couple of values:

    **proxy** - URL to ZAP. If running locally, it will be http://127.0.0.1:8080

    **attacklevel** - ZAP's Active Scan attack level. The values can be LOW, MEDIUM, HIGH, INSANE

Running the test
----------------

ZAP can be started in headless mode by running::

    ./zap.sh -daemon

To run the test::

    cd deuce/tests
    nosetests -s -v --with-xunit --nologcapture zap

The test script will shut down ZAP at the end
