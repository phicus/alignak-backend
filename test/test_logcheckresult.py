#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This test check the hostgroups and the tree feature of hostgroups (children)
"""

from __future__ import print_function
import json
import time
from datetime import datetime, timedelta
from calendar import timegm
import shlex
import subprocess
import copy
import requests
import unittest2


class TestActions(unittest2.TestCase):
    """
    This class test hostgroups and tree feature
    """

    @classmethod
    def setUpClass(cls):
        """
        This method:
          * delete mongodb database
          * start the backend with uwsgi
          * log in the backend and get the token
          * get the hostgroup

        :return: None
        """
        # Delete used mongo DBs
        exit_code = subprocess.call(
            shlex.split(
                'mongo %s --eval "db.dropDatabase()"' % 'alignak-backend'
            )
        )
        assert exit_code == 0

        cls.p = subprocess.Popen(['uwsgi', '-w', 'alignakbackend:app', '--socket', '0.0.0.0:5000',
                                  '--protocol=http', '--enable-threads', '--pidfile',
                                  '/tmp/uwsgi.pid'])
        time.sleep(3)

        cls.endpoint = 'http://127.0.0.1:5000'

        headers = {'Content-Type': 'application/json'}
        params = {'username': 'admin', 'password': 'admin', 'action': 'generate'}
        # get token
        response = requests.post(cls.endpoint + '/login', json=params, headers=headers)
        resp = response.json()
        cls.token = resp['token']
        cls.auth = requests.auth.HTTPBasicAuth(cls.token, '')

        # Get default realm
        response = requests.get(cls.endpoint + '/realm', auth=cls.auth)
        resp = response.json()
        cls.realm_all = resp['_items'][0]['_id']

        # Get admin user
        response = requests.get(cls.endpoint + '/user', {"name": "admin"}, auth=cls.auth)
        resp = response.json()
        cls.user_admin = resp['_items'][0]['_id']

    @classmethod
    def tearDownClass(cls):
        """
        Kill uwsgi

        :return: None
        """
        subprocess.call(['uwsgi', '--stop', '/tmp/uwsgi.pid'])
        time.sleep(2)

    @classmethod
    def setUp(cls):
        """
        Delete resources in backend

        :return: None
        """
        headers = {'Content-Type': 'application/json'}

        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = cls.realm_all
        requests.post(cls.endpoint + '/command', json=data, headers=headers, auth=cls.auth)
        response = requests.get(cls.endpoint + '/command', auth=cls.auth)
        resp = response.json()
        rc = resp['_items']

        # Add an host
        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        if 'realm' in data:
            del data['realm']
        data['_realm'] = cls.realm_all
        response = requests.post(cls.endpoint + '/host', json=data, headers=headers, auth=cls.auth)
        resp = response.json()
        print(resp)
        response = requests.get(cls.endpoint + '/host', auth=cls.auth)
        resp = response.json()
        print(resp)
        rh = resp['_items']

        # Add a service
        data = json.loads(open('cfg/service_srv001_ping.json').read())
        data['host'] = rh[0]['_id']
        data['check_command'] = rc[0]['_id']
        data['_realm'] = cls.realm_all
        requests.post(cls.endpoint + '/service', json=data, headers=headers, auth=cls.auth)

    @classmethod
    def tearDown(cls):
        """
        Delete resources in backend

        :return: None
        """
        for resource in ['host', 'service', 'command', 'history',
                         'logcheckresult']:
            requests.delete(cls.endpoint + '/' + resource, auth=cls.auth)

    def test_logcheckresult(self):
        # pylint: disable=too-many-locals
        """
        Test log checks results

        :return: None
        """
        headers = {'Content-Type': 'application/json'}
        sort_id = {'sort': '_id'}

        # No existing acknowledges
        response = requests.get(
            self.endpoint + '/logcheckresult', params=sort_id, auth=self.auth
        )
        resp = response.json()
        re = resp['_items']
        self.assertEqual(len(re), 0)

        # Get host in the backend
        response = requests.get(self.endpoint + '/host', auth=self.auth)
        resp = response.json()
        rh = resp['_items']
        self.assertEqual(rh[0]['name'], "srv001")

        # Get service in the backend
        response = requests.get(self.endpoint + '/service', auth=self.auth)
        resp = response.json()
        rs = resp['_items']
        self.assertEqual(rs[0]['name'], "ping")

        # -------------------------------------------
        # Add a check result
        data = {
            "last_check": timegm(datetime.utcnow().timetuple()),
            "host": rh[0]['_id'],
            "service": None,
            'acknowledged': False,
            'state_id': 0,
            'state': 'UP',
            'state_type': 'HARD',
            'last_state_id': 0,
            'last_state': 'UP',
            'last_state_type': 'HARD',
            'state_changed': False,
            'latency': 0,
            'execution_time': 0.12,
            'output': 'Check output',
            'long_output': 'Check long_output',
            'perf_data': 'perf_data',
            "_realm": self.realm_all
        }
        response = requests.post(
            self.endpoint + '/logcheckresult', json=data, headers=headers, auth=self.auth
        )
        resp = response.json()
        self.assertEqual(resp['_status'], 'OK')

        # Get check results
        response = requests.get(
            self.endpoint + '/logcheckresult', params=sort_id, auth=self.auth
        )
        resp = response.json()
        re = resp['_items']
        self.assertEqual(len(re), 1)
        re = resp['_items']
        check_id = re[0]['_id']

        self.assertEqual(re[0]['host'], rh[0]['_id'])
        self.assertEqual(re[0]['output'], 'Check output')

        # Get history
        response = requests.get(self.endpoint + '/history', params=sort_id, auth=self.auth)
        resp = response.json()
        re = resp['_items']
        self.assertEqual(len(re), 1)

        self.assertEqual(re[0]['host'], rh[0]['_id'])
        self.assertEqual(re[0]['service'], None)
        self.assertEqual(re[0]['type'], "check.result")
        self.assertEqual(re[0]['message'], "")
        self.assertEqual(re[0]['check_result'], check_id)
