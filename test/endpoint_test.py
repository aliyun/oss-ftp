# -*- coding: utf-8 -*-

from util import *
from common.util import wrap_protocol
import unittest

class EnpointTest(unittest.TestCase):
    def test_wrap_with_protocol(self):
        endpoint = 'oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'http')
        self.assertEqual('http://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)

        endpoint = 'oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'https')
        self.assertEqual('https://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)

        endpoint = 'http://oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'http')
        self.assertEqual('http://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)

        endpoint = 'http://oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'https')
        self.assertEqual('https://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)


        endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'https')
        self.assertEqual('https://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)

        endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
        wrapped_endpoint = wrap_protocol(endpoint, 'http')
        self.assertEqual('http://oss-cn-hangzhou.aliyuncs.com', wrapped_endpoint)

    def test_endpoint_none(self):
        endpoint = None
        wrapped_endpoint = wrap_protocol(endpoint, 'http')
        self.assertIsNone(wrapped_endpoint)


if __name__ == '__main__':
    print('\n\nstart test %s' % __file__)
    unittest.main()
