import unittest
import sys

import wfuzz

try:
    # Python >= 3.3
    from unittest import mock
except ImportError:
    # Python < 3.3
    import mock

LOCAL_DOMAIN = "http://localhost"
URL_LOCAL = "%s:8000/dir" % (LOCAL_DOMAIN)
HTTPD_PORT = 8000

ECHO_URL = "%s:8000/echo" % (LOCAL_DOMAIN)


class APITests(unittest.TestCase):
    def test_get_payload(self):
        payload_list = wfuzz.get_payload(list(range(4))).data.get('dictio')[0]
        self.assertEqual(sorted(payload_list), sorted([0, 1, 2, 3]))

    def test_get_payloads(self):
        payload_list = wfuzz.get_payload([list(range(2)), list(range(2))]).data.get('dictio')[0]
        self.assertEqual(sorted(payload_list), sorted([[0, 1], [0, 1]]))

    def test_encoders(self):
        encoders = {
            'none': ('test', 'test'),
            'urlencode': ("../=?&", '../%3D%3F%26'),
            'double_urlencode': ("../=?&", '../%253D%253F%2526'),
            'double_urlencode': ("../=?&", '../%253D%253F%2526'),
            'base64': ('admin', 'YWRtaW4='),

            'sha1': ('admin', 'd033e22ae348aeb5660fc2140aec35850c4da997'),
            'md5': ('admin', '21232f297a57a5a743894a0e4a801fc3'),
            'hexlify': ('admin', '61646d696e'),
            'html_escape': ('<>&\'"/', "&lt;&gt;&amp;&#x27;&quot;/"),
            'html_decimal': ('<>&\'"/', '&#60;&#62;&#38;&#39;&#34;&#47;'),
            'html_hexadecimal': ('<>&\'"/', '&#x3c;&#x3e;&#x26;&#x27;&#x22;&#x2f;'),

            'mysql_char': ('admin', 'CHAR(97,100,109,105,110)'),
            'mssql_char': ('admin', 'CHAR(97)+CHAR(100)+CHAR(109)+CHAR(105)+CHAR(110)'),
            'oracle_char': ('admin', 'chr(97)||chr(100)||chr(109)||chr(105)||chr(110)'),
        }

        for key, values in list(encoders.items()):
            value, expected = values
            self.assertEqual(wfuzz.encode(key, value), expected)

        for key, values in [items for items in list(encoders.items()) if items[0] not in ['html_hexadecimal', 'html_decimal', 'md5', 'sha1', 'html_escape']]:
            value, expected = values
            self.assertEqual(wfuzz.decode(key, expected), value)

    def test_decode(self):
        payload_list = wfuzz.get_payload([list(range(2)), list(range(2))]).data.get('dictio')[0]
        self.assertEqual(sorted(payload_list), sorted([[0, 1], [0, 1]]))

    def test_get_session(self):
        data = wfuzz.get_session('-z range,0-4 http://127.0.0.1/FUZZ').data

        self.assertEqual(data.get('url'), 'http://127.0.0.1/FUZZ')
        self.assertEqual(data.get('payloads'), [('range', {'default': '0-4', 'encoder': None}, None)])

    def test_payload(self):
        payload_list = list(wfuzz.payload(**{'payloads': [('range', {'default': '0-4', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('0',), ('1',), ('2',), ('3',), ('4',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('buffer_overflow', {'default': '10', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('AAAAAAAAAA',)])

        with mock.patch('os.walk') as mocked_oswalk:
            mocked_oswalk.return_value = [
                ('foo', ('bar',), ('baz',)),
                ('foo/bar', (), ('spam', 'eggs')),
            ]
            payload_list = list(wfuzz.payload(**{'payloads': [('dirwalk', {'default': 'foo', 'encoder': None}, None)]}))
            self.assertEqual(payload_list, [('baz',), ('bar/spam',), ('bar/eggs',)])

        mocked_fun = "builtins.open" if sys.version_info >= (3, 0) else "__builtin__.open"
        with mock.patch(mocked_fun, mock.mock_open(read_data="one\ntwo\n")):
            payload_list = list(wfuzz.payload(**{'payloads': [('file', {'default': 'mockedfile', 'encoder': None}, None)]}))
            self.assertEqual(payload_list, [('one',), ('two',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('hexrange', {'default': '09-10', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('09',), ('0a',), ('0b',), ('0c',), ('0d',), ('0e',), ('0f',), ('10',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('hexrange', {'default': '009-00B', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('009',), ('00a',), ('00b',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('ipnet', {'default': '192.168.0.1/30', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('192.168.0.1',), ('192.168.0.2',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('iprange', {'default': '192.168.0.1-192.168.0.2', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('192.168.0.1',), ('192.168.0.2',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('list', {'default': 'a-b', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('a',), ('b',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('list', {'default': 'a\-b-b', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('a-b',), ('b',)])

        payload_list = list(wfuzz.payload(**{'payloads': [('range', {'default': '1-2', 'encoder': None}, None)]}))
        self.assertEqual(payload_list, [('1',), ('2',)])

    def test_iterator(self):
        payload_list = list(wfuzz.payload(**{'iterator': 'zip', 'payloads': [('range', {'default': '0-2', 'encoder': None}, None), ('range', {'default': '0-2', 'encoder': None}, None)]}))
        self.assertEqual(sorted(payload_list), sorted([('0', '0'), ('1', '1'), ('2', '2')]))

        payload_list = list(wfuzz.payload(**{'iterator': 'chain', 'payloads': [('range', {'default': '0-2', 'encoder': None}, None), ('range', {'default': '0-2', 'encoder': None}, None)]}))
        self.assertEqual(sorted(payload_list), sorted([('0',), ('0',), ('1',), ('1',), ('2',), ('2',)]))

        payload_list = list(wfuzz.payload(**{'iterator': 'product', 'payloads': [('range', {'default': '0-2', 'encoder': None}, None), ('range', {'default': '0-2', 'encoder': None}, None)]}))
        self.assertEqual(sorted(payload_list), sorted([('0', '0'), ('0', '1'), ('0', '2'), ('1', '0'), ('1', '1'), ('1', '2'), ('2', '0'), ('2', '1'), ('2', '2')]))


if __name__ == '__main__':
        unittest.main()
