#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import requests
import time
import subprocess
import json
from alignak_backend_client.client import Backend
from alignak_backend.models.host import get_schema as host_schema


class TestHookTemplate(unittest2.TestCase):

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.p = subprocess.Popen(['uwsgi', '-w', 'alignakbackend:app', '--socket', '0.0.0.0:5000', '--protocol=http', '--enable-threads'])
        time.sleep(3)
        cls.backend = Backend('http://127.0.0.1:5000')
        cls.backend.login("admin", "admin", "force")
        cls.backend.delete("host", {})
        cls.backend.delete("command", {})
        cls.backend.delete("livestate", {})
        cls.backend.delete("livesynthesis", {})
        realms = cls.backend.get_all('realm')
        for cont in realms:
            cls.realm_all = cont['_id']

    @classmethod
    def tearDownClass(cls):
        cls.backend.delete("contact", {})
        cls.p.kill()

    @classmethod
    def tearDown(cls):
        cls.backend.delete("host", {})
        cls.backend.delete("service", {})
        cls.backend.delete("command", {})
        cls.backend.delete("livestate", {})
        cls.backend.delete("livesynthesis", {})

    def test_host_templates(self):
        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)
        # Check if command right in backend
        rc = self.backend.get_all('command')
        self.assertEqual(rc[0]['name'], "ping")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['realm'] = self.realm_all
        data['_is_template'] = True
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        data = {
            'name': 'host_001',
            '_templates': [rh[0]['_id']],
            'realm': self.realm_all
        }
        self.backend.post("host", data)

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")
        self.assertEqual(rh[1]['name'], "host_001")
        self.assertEqual(rh[1]['check_command'], rc[0]['_id'])

        schema = host_schema()
        template_fields = []
        ignore_fields = ['name', 'realm', '_template_fields', '_templates', '_is_template',
                         '_templates_with_services']
        for key in schema['schema'].iterkeys():
            if key not in ignore_fields:
                template_fields.append(key)

        self.assertItemsEqual([x.encode('UTF8') for x in rh[1]['_template_fields']], template_fields)

        data = [{
            'name': 'host_002',
            '_templates': [rh[0]['_id']],
            'realm': self.realm_all
        }, {
            'name': 'host_003',
            '_templates': [rh[0]['_id']],
            'realm': self.realm_all
        }]
        self.backend.post("host", data)

        rh = self.backend.get_all('host')
        self.assertEqual(rh[2]['name'], "host_002")
        self.assertEqual(rh[3]['name'], "host_003")

    def test_host_templates_updates(self):
        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)
        # Check if command right in backend
        rc = self.backend.get_all('command')
        self.assertEqual(rc[0]['name'], "ping")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['realm'] = self.realm_all
        data['_is_template'] = True
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        data = {
            'name': 'host_001',
            '_templates': [rh[0]['_id']],
            'realm': self.realm_all
        }
        self.backend.post("host", data)

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")
        self.assertEqual(rh[1]['name'], "host_001")
        self.assertEqual(rh[1]['check_command'], rc[0]['_id'])

        data = {'check_interval': 1}
        resp = self.backend.patch('/'.join(['host', rh[1]['_id']]), data, {'If-Match': rh[1]['_etag']})

        rh = self.backend.get_all('host')
        self.assertEqual(rh[1]['name'], "host_001")
        self.assertEqual(rh[1]['check_interval'], 1)
        if 'check_interval' in rh[1]['_template_fields']:
            self.assertTrue(False, 'check_interval does not be in _template_fields list')

        # update the template
        data = {'initial_state': 'o'}
        self.backend.patch('/'.join(['host', rh[0]['_id']]), data, {'If-Match': rh[0]['_etag']})

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['initial_state'], "o")
        self.assertEqual(rh[1]['name'], "host_001")
        self.assertEqual(rh[1]['initial_state'], "o")
        if 'initial_state' not in rh[1]['_template_fields']:
            self.assertTrue(False, 'initial_state must be in _template_fields list')

        # update the template name
        data = {'name': 'testhost'}
        self.backend.patch('/'.join(['host', rh[0]['_id']]), data, {'If-Match': rh[0]['_etag']})

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "testhost")
        self.assertEqual(rh[1]['name'], "host_001")

    def test_service_templates(self):
        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)
        # Check if command right in backend
        rc = self.backend.get_all('command')
        self.assertEqual(rc[0]['name'], "ping")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['realm'] = self.realm_all
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['name'] = 'host_001'
        data['realm'] = self.realm_all
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")
        self.assertEqual(rh[1]['name'], "host_001")

        # add service template
        data = {
            'name': 'ping',
            'host_name': rh[0]['_id'],
            'check_command': rc[0]['_id'],
            'business_impact': 4,
            '_is_template': True,
            '_realm': self.realm_all
        }
        self.backend.post("service", data)
        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['name'], "ping")

        data = {
            'host_name': rh[1]['_id'],
            '_templates': [rs[0]['_id']],
            '_realm': self.realm_all
        }
        self.backend.post("service", data)

        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['name'], "ping")
        self.assertEqual(rs[1]['name'], "ping")
        self.assertEqual(rs[1]['host_name'], rh[1]['_id'])

    def test_service_templates_updates(self):
        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)
        # Check if command right in backend
        rc = self.backend.get_all('command')
        self.assertEqual(rc[0]['name'], "ping")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['realm'] = self.realm_all
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['name'] = 'host_001'
        data['realm'] = self.realm_all
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")

        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "srv001")
        self.assertEqual(rh[1]['name'], "host_001")

        # add service template
        data = {
            'name': 'ping',
            'host_name': rh[0]['_id'],
            'check_command': rc[0]['_id'],
            'business_impact': 4,
            '_is_template': True,
            '_realm': self.realm_all
        }
        self.backend.post("service", data)
        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['name'], "ping")

        data = {
            'name': 'ping_test',
            'host_name': rh[1]['_id'],
            '_templates': [rs[0]['_id']],
            '_realm': self.realm_all
        }
        self.backend.post("service", data)

        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['name'], "ping")
        self.assertEqual(rs[1]['name'], "ping_test")
        self.assertEqual(rs[1]['host_name'], rh[1]['_id'])

        data = {'check_interval': 1}
        resp = self.backend.patch('/'.join(['service', rs[1]['_id']]), data, {'If-Match': rs[1]['_etag']})

        rs = self.backend.get_all('service')
        self.assertEqual(rs[1]['name'], "ping_test")
        self.assertEqual(rs[1]['check_interval'], 1)
        if 'check_interval' in rs[1]['_template_fields']:
            self.assertTrue(False, 'check_interval does not be in _template_fields list')

        # update the template
        data = {'initial_state': 'u'}
        self.backend.patch('/'.join(['service', rs[0]['_id']]), data, {'If-Match': rs[0]['_etag']})

        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['initial_state'], "u")
        self.assertEqual(rs[1]['name'], "ping_test")
        self.assertEqual(rs[1]['initial_state'], "u")
        if 'initial_state' not in rs[1]['_template_fields']:
            self.assertTrue(False, 'initial_state must be in _template_fields list')

        # update the template name
        data = {'name': 'ping2'}
        self.backend.patch('/'.join(['service', rs[0]['_id']]), data, {'If-Match': rs[0]['_etag']})

        rs = self.backend.get_all('service')
        self.assertEqual(rs[0]['name'], "ping2")
        self.assertEqual(rs[1]['name'], "ping_test")


    def test_host_services_template(self):
        # Add command
        data = json.loads(open('cfg/command_ping.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)

        data = json.loads(open('cfg/command_http.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)

        data = json.loads(open('cfg/command_https.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)

        data = json.loads(open('cfg/command_ssh.json').read())
        data['_realm'] = self.realm_all
        self.backend.post("command", data)

        # Check if command right in backend
        rc = self.backend.get_all('command')
        self.assertEqual(rc[0]['name'], "ping")
        self.assertEqual(rc[1]['name'], "http")
        self.assertEqual(rc[2]['name'], "https")
        self.assertEqual(rc[3]['name'], "ssh")

        # Add host templates
        data = json.loads(open('cfg/host_srv001.json').read())
        data['check_command'] = rc[0]['_id']
        data['realm'] = self.realm_all
        data['name'] = 'template_standard_linux'
        data['_is_template'] = True
        self.backend.post("host", data)
        data['name'] = 'template_web'
        self.backend.post("host", data)
        # Check if host right in backend
        rh = self.backend.get_all('host')
        self.assertEqual(rh[0]['name'], "template_standard_linux")
        self.assertEqual(rh[1]['name'], "template_web")

        # Add services templates
        data = {
            'name': 'ping',
            'host_name': rh[0]['_id'],
            'check_command': rc[0]['_id'],
            'business_impact': 4,
            '_is_template': True,
            '_realm': self.realm_all
        }
        self.backend.post("service", data)
        data['name'] = 'ssh'
        data['check_command'] = rc[3]['_id']
        self.backend.post("service", data)
        data['name'] = 'http'
        data['host_name'] = rh[1]['_id']
        data['check_command'] = rc[1]['_id']
        self.backend.post("service", data)
        data['name'] = 'https'
        data['check_command'] = rc[2]['_id']
        self.backend.post("service", data)
        params = {'sort': '_id'}
        rs = self.backend.get_all('service', params)
        self.assertEqual(rs[0]['name'], "ping")
        self.assertEqual(rs[1]['name'], "ssh")
        self.assertEqual(rs[2]['name'], "http")
        self.assertEqual(rs[3]['name'], "https")

        # add a host with host template + allow service templates
        data = {
            'name': 'host_001',
            '_templates': [rh[0]['_id'], rh[1]['_id']],
            '_templates_with_services': True,
            'realm': self.realm_all
        }
        self.backend.post("host", data)
        rh = self.backend.get_all('host')
        self.assertEqual(rh[2]['name'], "host_001")
        rs = self.backend.get_all('service', params)
        self.assertEqual(len(rs), 8)
        self.assertEqual(rs[4]['name'], "http")
        self.assertEqual(rs[5]['_is_template'], False)
        self.assertEqual(rs[5]['name'], "ping")
        self.assertEqual(rs[6]['name'], "ssh")
        self.assertEqual(rs[7]['name'], "https")

        # Now update a service template
        data = {'name': 'ping2'}
        self.backend.patch('/'.join(['service', rs[0]['_id']]), data, {'If-Match': rs[0]['_etag']})
        rs = self.backend.get_all('service', params)
        self.assertEqual(rs[0]['name'], "ping2")
        self.assertEqual(rs[5]['name'], "ping2")

        # Now remove the template template_web of the host
        data = {'_templates': [rh[0]['_id']]}
        resp = self.backend.patch('/'.join(['host', rh[2]['_id']]), data,
                                  {'If-Match': rh[2]['_etag']})
        rs = self.backend.get_all('service')
        self.assertEqual(len(rs), 6)
        rh = self.backend.get_all('host')
        self.assertEqual(rh[2]['_templates'], [rh[0]['_id']])

        # Now re-add the template template_web of host
        data = {'_templates': [rh[0]['_id'], rh[1]['_id']]}
        resp = self.backend.patch('/'.join(['host', rh[2]['_id']]), data,
                                  {'If-Match': rh[2]['_etag']})
        rs = self.backend.get_all('service')
        self.assertEqual(len(rs), 8)

        # Now add a new template
        data = {
            'name': 'ssh_new_method',
            'host_name': rh[0]['_id'],
            'check_command': rc[0]['_id'],
            'business_impact': 4,
            '_is_template': True,
            '_templates_from_host_template': True,
            '_realm': self.realm_all
        }
        ret_new = self.backend.post("service", data)
        rs = self.backend.get_all('service', params)
        self.assertEqual(len(rs), 10)
        self.assertEqual(rs[9]['_templates'][0], ret_new['_id'])
        self.assertFalse(rs[9]['_is_template'])
        self.assertEqual(rs[8]['_templates'], [])
        self.assertTrue(rs[8]['_is_template'])

        # Now delete a new template
        rs = self.backend.get('/'.join(['service', ret_new['_id']]))
        self.backend.delete('/'.join(['service', ret_new['_id']]), {'If-Match': rs['_etag']})
        rs = self.backend.get_all('service', params)
        service_name = []
        for serv in rs:
            service_name.append(serv['name'])
        self.assertEqual(len(rs), 8)
        self.assertEqual(['ping2', 'ssh', 'http', 'https', 'ping2', 'ssh', 'http', 'https'], service_name)