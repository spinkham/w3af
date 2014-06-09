"""
test_create_fuzzable_request.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.querystring_request import QsRequest
from w3af.core.data.request.json_request import JSONPostDataRequest
from w3af.core.data.request.xmlrpc_request import XMLRPCRequest
from w3af.core.data.request.multipart_request import MultipartRequest
from w3af.core.data.request.urlencoded_post_request import URLEncPostRequest
from w3af.core.data.url.handlers.multipart import multipart_encode
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.kv_container import KeyValueContainer
from w3af.core.data.request.factory import (create_fuzzable_request_from_parts,
                                            create_fuzzable_request_from_request)


@attr('smoke')
class TestCreateFuzzableRequestFromParts(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')

    def test_simplest(self):
        fr = create_fuzzable_request_from_parts(self.url)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), Headers())
        self.assertEqual(fr.get_method(), 'GET')

    def test_headers(self):
        hdr = Headers([('foo', 'bar')])
        fr = create_fuzzable_request_from_parts(self.url, add_headers=hdr)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'GET')

    def test_headers_method(self):
        hdr = Headers([('foo', 'bar')])
        fr = create_fuzzable_request_from_parts(self.url, method='PUT',
                                                add_headers=hdr)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'PUT')

    def test_simple_post(self):
        post_data = 'a=b&d=3'
        hdr = Headers([('content-length', str(len(post_data))),
                       ('content-type', URLEncPostRequest.ENCODING)])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=hdr,
                                                post_data=post_data,
                                                method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIn('content-type', fr.get_headers())
        self.assertIsInstance(fr, URLEncPostRequest)

    def test_json_post(self):
        post_data = '{"1":"2"}'
        hdr = Headers([('content-length', str(len(post_data))),
                       ('content-type', 'application/json')])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=hdr,
                                                post_data=post_data,
                                                method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIsInstance(fr, JSONPostDataRequest)

    def test_json_creation_missing_header(self):
        post_data = '{"1":"2"}'
        # Missing the content-type header for json
        hdr = Headers([('content-length', str(len(post_data)))])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=hdr,
                                                post_data=post_data,
                                                method='POST')

        self.assertIs(fr, None)

    def test_xmlrpc_post(self):
        post_data = """<methodCall>
            <methodName>system.listMethods</methodName>
            <params></params>
        </methodCall>"""

        headers = Headers([('content-length', str(len(post_data)))])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=headers,
                                                post_data=post_data,
                                                method='POST')

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), headers)
        self.assertEqual(fr.get_method(), 'POST')
        self.assertIsInstance(fr, XMLRPCRequest)

    def test_multipart_post(self):
        boundary, post_data = multipart_encode([('a', 'bcd'), ], [])
        multipart_boundary = 'multipart/form-data; boundary=%s'

        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', multipart_boundary % boundary)])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=headers,
                                                post_data=post_data,
                                                method='POST')

        expected_headers = Headers([('content-type',
                                     multipart_boundary % boundary)])

        self.assertIsInstance(fr, MultipartRequest)
        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), expected_headers)
        self.assertIn('multipart/form-data', fr.get_headers()['content-type'])
        self.assertEqual(fr.get_method(), 'POST')
        self.assertEqual(fr.get_dc(),
                         KeyValueContainer(init_val=[('a', ['bcd'])]))

    def test_invalid_multipart_post(self):
        _, post_data = multipart_encode([('a', 'bcd'), ], [])

        # It is invalid because there is a missing boundary parameter in the
        # content-type header
        headers = Headers([('content-length', str(len(post_data))),
                           ('content-type', 'multipart/form-data')])

        fr = create_fuzzable_request_from_parts(self.url, add_headers=headers,
                                                post_data=post_data,
                                                method='POST')

        self.assertIsNone(fr)

@attr('smoke')
class TestCreateFuzzableRequestRequest(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')

    def test_from_HTTPRequest(self):
        request = HTTPRequest(self.url)
        fr = create_fuzzable_request_from_request(request)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_method(), 'GET')

    def test_from_HTTPRequest_headers(self):
        hdr = Headers([('Foo', 'bar')])
        request = HTTPRequest(self.url, headers=hdr)
        fr = create_fuzzable_request_from_request(request)

        self.assertEqual(fr.get_url(), self.url)
        self.assertEqual(fr.get_headers(), hdr)
        self.assertEqual(fr.get_method(), 'GET')
        self.assertIsInstance(fr, QsRequest)
