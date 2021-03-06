# coding=utf-8
"""Test related to the api docs page."""
import unittest

from requests.exceptions import HTTPError

from pulp_smash import api, config, selectors, utils
from pulp_smash.tests.pulp3.constants import API_DOCS_PATH
from pulp_smash.tests.pulp3.pulpcore.utils import set_up_module as setUpModule  # pylint:disable=unused-import


class ApiDocsTestCase(unittest.TestCase, utils.SmokeTest):
    """Test whether API auto generated docs are available.

    This test targets the following issues:

    * `Pulp #3552 <https://pulp.plan.io/issues/3552>`_
    * `Pulp Smash #893 <https://github.com/PulpQE/pulp-smash/issues/893>`_
    """

    def setUp(self):
        """Create an API Client."""
        cfg = config.get_config()
        if selectors.bug_is_untestable(3552, cfg.pulp_version):
            self.skipTest('https://pulp.plan.io/issues/3552')
        self.client = api.Client(cfg)

    def test_valid_credentials(self):
        """Get API documentation with valid credentials.

        Assert the API documentation is returned.
        """
        self.client.get(API_DOCS_PATH)

    def test_no_credentials(self):
        """Get API documentation with no credentials.

        Assert the API documentation is returned.
        """
        del self.client.request_kwargs['auth']
        self.client.get(API_DOCS_PATH)

    def test_http_method(self):
        """Get API documentation with an HTTP method other than GET.

        Assert an error is returned.
        """
        with self.assertRaises(HTTPError):
            self.client.post(API_DOCS_PATH)
