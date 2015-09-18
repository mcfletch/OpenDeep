from __future__ import print_function
import unittest
from ..standard_datasets.tedlium import sph

class TestSPH(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    SAMPLE_HEADER = '''NIST_1A
   1024
sample_count -i 5821336
sample_n_bytes -i 2
channel_count -i 1
sample_byte_format -s2 01
sample_rate -i 16000
sample_coding -s3 pcm
end_head'''
    EXPECTED_FORMAT = {
        'sample_sig_bits': 16,
        'sample_n_bytes': 2,
        'channel_count': 1,
        'sample_byte_format': '01',
        'sample_rate': 16000,
        'sample_coding': 'pcm',
        'big_endian': False,
        'gst_format': 'U16LE' if sph.MACHINE_LE else 'U16BE',
    }
    def test_sph_format_parser(self):
        format = sph.parse_sph_header(self.SAMPLE_HEADER)
        assert format == self.EXPECTED_FORMAT,format


if __name__ == '__main__':
    unittest.main()
