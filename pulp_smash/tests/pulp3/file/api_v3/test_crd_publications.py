# coding=utf-8
"""Tests that perform actions over publications."""
import unittest
from urllib.parse import urljoin

from requests.exceptions import HTTPError

from pulp_smash import api, config, selectors, utils
from pulp_smash.constants import FILE_FEED_URL
from pulp_smash.tests.pulp3.constants import (
    DISTRIBUTION_PATH,
    FILE_PUBLISHER_PATH,
    FILE_REMOTE_PATH,
    PUBLICATIONS_PATH,
    REPO_PATH,
)
from pulp_smash.tests.pulp3.file.api_v3.utils import (
    gen_remote,
    gen_publisher,
)
from pulp_smash.tests.pulp3.file.utils import set_up_module as setUpModule  # pylint:disable=unused-import
from pulp_smash.tests.pulp3.pulpcore.utils import gen_distribution, gen_repo
from pulp_smash.tests.pulp3.utils import (
    get_auth,
    publish_repo,
    sync_repo,
)


class PublicationsTestCase(unittest.TestCase, utils.SmokeTest):
    """Perform actions over publications."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variables."""
        cls.cfg = config.get_config()
        cls.client = api.Client(cls.cfg, api.json_handler)
        cls.client.request_kwargs['auth'] = get_auth()
        cls.remote = {}
        cls.publication = {}
        cls.publisher = {}
        cls.repo = {}
        try:
            cls.repo.update(cls.client.post(REPO_PATH, gen_repo()))
            body = gen_remote()
            body['url'] = urljoin(FILE_FEED_URL, 'PULP_MANIFEST')
            cls.remote.update(cls.client.post(FILE_REMOTE_PATH, body))
            cls.publisher.update(
                cls.client.post(FILE_PUBLISHER_PATH, gen_publisher())
            )
            sync_repo(cls.cfg, cls.remote, cls.repo)
        except:  # noqa:E722
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean class-wide variables."""
        for resource in (cls.remote, cls.publisher, cls.repo):
            if resource:
                cls.client.delete(resource['_href'])

    def test_01_create_publication(self):
        """Create a publication."""
        self.publication.update(
            publish_repo(self.cfg, self.publisher, self.repo)
        )

    @selectors.skip_if(bool, 'publication', False)
    def test_02_read_publication(self):
        """Read a publication by its href."""
        publication = self.client.get(self.publication['_href'])
        for key, val in self.publication.items():
            with self.subTest(key=key):
                self.assertEqual(publication[key], val)

    @selectors.skip_if(bool, 'publication', False)
    def test_02_read_publications(self):
        """Read a publication by its repository version."""
        page = self.client.get(PUBLICATIONS_PATH, params={
            'repository_version': self.repo['_href']
        })
        self.assertEqual(len(page['results']), 1)
        for key, val in self.publication.items():
            with self.subTest(key=key):
                self.assertEqual(page['results'][0][key], val)

    @selectors.skip_if(bool, 'publication', False)
    def test_03_read_publications(self):
        """Read a publication by its publisher."""
        page = self.client.get(PUBLICATIONS_PATH, params={
            'publisher': self.publisher['_href']
        })
        self.assertEqual(len(page['results']), 1)
        for key, val in self.publication.items():
            with self.subTest(key=key):
                self.assertEqual(page['results'][0][key], val)

    @selectors.skip_if(bool, 'publication', False)
    def test_04_read_publications(self):
        """Read a publication by its created time."""
        page = self.client.get(PUBLICATIONS_PATH, params={
            'created': self.publication['created']
        })
        self.assertEqual(len(page['results']), 1)
        for key, val in self.publication.items():
            with self.subTest(key=key):
                self.assertEqual(page['results'][0][key], val)

    @selectors.skip_if(bool, 'publication', False)
    def test_05_read_publications(self):
        """Read a publication by its distribution."""
        body = gen_distribution()
        body['publication'] = self.publication['_href']
        distribution = self.client.post(DISTRIBUTION_PATH, body)
        self.addCleanup(self.client.delete, distribution['_href'])
        self.publication.update(self.client.get(self.publication['_href']))
        page = self.client.get(PUBLICATIONS_PATH, params={
            'distributions': distribution['_href']
        })
        self.assertEqual(len(page['results']), 1)
        for key, val in self.publication.items():
            with self.subTest(key=key):
                self.assertEqual(page['results'][0][key], val)

    @selectors.skip_if(bool, 'publication', False)
    def test_06_delete(self):
        """Delete a publication."""
        if selectors.bug_is_untestable(3354, self.cfg.pulp_version):
            self.skipTest('https://pulp.plan.io/issues/3354')
        self.client.delete(self.publication['_href'])
        with self.assertRaises(HTTPError):
            self.client.get(self.publication['_href'])
