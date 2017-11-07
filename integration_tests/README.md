# Blender ID Integration Tests

These tests are made to run against a live server; this can be either production, test,
or development server).

## Setting up & running

The tests require the following environment variables:

- `BLENDER_ID_ENDPOINT`: the URL of the Blender ID server under test. For example
  http://blender-id:8000/ for a typical dev server.
- `BCLOUD_SERVER`: the Blender Cloud server, used for sending subclient tokens. For example
  http://blender-cloud:5000/ for a typical dev server.

The following environment variables are optional and provide extra convenience:

- `BLENDER_ID_UNAME`: valid username for login/token creation/revocation etc. tests. If not given,
  the test will prompt for it.
- `BLENDER_ID_PASSWD`: valid password for said tests. If not given, the test will prompt for it.
  Note that using this environment variable is convenient but may also be a security leak (since any
  process can inspect other processes' environment variables).

The tests can be run using `py.test integration_tests`, or `cd integration_tests; py.test`.

The `-s` option prevents capture of stdin/out and is required as some tests require user
interaction; this option is passed automatically to Py.Test when it's run as described above, due to
its inclusion in `integration_tests/setup.cfg`.
