# coding=utf-8
"""Tests that perform action over remotes and publishers."""

import unittest
from urllib.parse import urljoin

from pulp_smash import api, config, selectors, utils
from pulp_smash.constants import FILE_FEED_URL
from pulp_smash.tests.pulp3.constants import (
    FILE_REMOTE_PATH,
    FILE_PUBLISHER_PATH,
    REPO_PATH,
)
from pulp_smash.tests.pulp3.file.api_v3.utils import (
    gen_remote,
    gen_publisher,
)
from pulp_smash.tests.pulp3.file.utils import set_up_module as setUpModule  # pylint:disable=unused-import
from pulp_smash.tests.pulp3.pulpcore.utils import gen_repo
from pulp_smash.tests.pulp3.utils import (
    get_auth,
    get_content,
    publish_repo,
    sync_repo,
)


class RemotesPublishersTestCase(unittest.TestCase, utils.SmokeTest):
    """Verify publisher and remote can be used with different repos."""

    def test_all(self):
        """Verify publisher and remote can be used with different repos.

        This test explores the design choice stated in `Pulp #3341`_ that
        remove the FK from publishers and remotes to repository.
        Allowing remotes and publishers to be used with different
        repositories.

        .. _Pulp #3341: https://pulp.plan.io/issues/3341

        Do the following:

        1. Create an remote, and a publisher.
        2. Create 2 repositories.
        3. Sync both repositories using the same remote.
        4. Assert that the two repositories have the same contents.
        5. Publish both repositories using the same publisher.
        6. Assert that each generated publication has the same publisher, but
           are associated with different repositories.
        """
        cfg = config.get_config()
        if selectors.bug_is_untestable(3502, cfg.pulp_version):
            self.skipTest('https://pulp.plan.io/issues/3502')

        # Create an remote and publisher.
        client = api.Client(cfg, api.json_handler)
        client.request_kwargs['auth'] = get_auth()
        body = gen_remote()
        body['url'] = urljoin(FILE_FEED_URL, 'PULP_MANIFEST')
        remote = client.post(FILE_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote['_href'])
        publisher = client.post(FILE_PUBLISHER_PATH, gen_publisher())
        self.addCleanup(client.delete, publisher['_href'])

        # Create and sync repos.
        repos = []
        for _ in range(2):
            repo = client.post(REPO_PATH, gen_repo())
            self.addCleanup(client.delete, repo['_href'])
            sync_repo(cfg, remote, repo)
            repos.append(client.get(repo['_href']))

        # Compare contents of repositories.
        contents = []
        for repo in repos:
            contents.append(get_content(repo)['results'])
        self.assertEqual(
            {content['_href'] for content in contents[0]},
            {content['_href'] for content in contents[1]},
        )

        # Publish repositories.
        publications = []
        for repo in repos:
            publications.append(publish_repo(cfg, publisher, repo))
            if selectors.bug_is_testable(3354, cfg.pulp_version):
                self.addCleanup(client.delete, publications[-1]['_href'])
        self.assertEqual(
            publications[0]['publisher'],
            publications[1]['publisher']
        )
        self.assertNotEqual(
            publications[0]['repository_version'],
            publications[1]['repository_version']
        )
