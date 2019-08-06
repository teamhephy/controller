"""
Unit tests for the Deis scheduler module.

Run the tests with "./manage.py test scheduler"
"""
import requests
import requests_mock
from unittest import mock
from packaging.version import parse

from django.test import TestCase

import scheduler


def mock_session_for_version(blah=None):
    return requests.Session()


def connection_refused_matcher(request):
    raise requests.ConnectionError("connection refused")


@mock.patch('scheduler.get_session', mock_session_for_version)
class KubeHTTPClientTest(TestCase):
    """Tests kubernetes HTTP client version calls"""

    def setUp(self):
        self.adapter = requests_mock.Adapter()
        self.url = 'http://versiontest.example.com'
        self.path = '/version'

        # use the real scheduler client.
        self.scheduler = scheduler.KubeHTTPClient(self.url)
        self.scheduler.session.mount(self.url, self.adapter)

    def test_version_for_gke(self):
        """
        Ensure that version() sanitizes info from GKE clusters
        """

        cases = {
                "1.12": {"major": "1", "minor": "12-gke"},
                "1.10": {"major": "1", "minor": "10-gke"},
                "1.9": {"major": "1", "minor": "9-gke"},
                "1.8": {"major": "1", "minor": "8-gke"},
                }

        for canonical in cases:
            resp = cases[canonical]
            self.adapter.register_uri('GET', self.url + self.path, json=resp)

            expected = parse(canonical)
            actual = self.scheduler.version()

            self.assertEqual(expected, actual, "{} breaks".format(resp))

    def test_version_for_eks(self):
        """
        Ensure that version() sanitizes info from EKS clusters
        """

        cases = {
                "1.12": {"major": "1", "minor": "12+"},
                "1.10": {"major": "1", "minor": "10+"},
                "1.9": {"major": "1", "minor": "9+"},
                "1.8": {"major": "1", "minor": "8+"},
                }

        for canonical in cases:
            resp = cases[canonical]
            self.adapter.register_uri('GET', self.url + self.path, json=resp)

            expected = parse(canonical)
            actual = self.scheduler.version()

            self.assertEqual(expected, actual, "{} breaks".format(resp))

    def test_version_vanilla(self):
        """
        Ensure that version() sanitizes info from vanilla k8s clusters
        """

        cases = {
                "1.12": {"major": "1", "minor": "12"},
                "1.10": {"major": "1", "minor": "10"},
                "1.9": {"major": "1", "minor": "9"},
                "1.8": {"major": "1", "minor": "8"},
                }

        for canonical in cases:
            resp = cases[canonical]
            self.adapter.register_uri('GET', self.url + self.path, json=resp)

            expected = parse(canonical)
            actual = self.scheduler.version()

            self.assertEqual(expected, actual, "{} breaks".format(resp))
