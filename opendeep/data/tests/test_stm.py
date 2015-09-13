# standard libraries
from __future__ import print_function
import unittest
#import numpy
#from opendeep.log.logger import config_root_logger
from ..standard_datasets.tedlium import stm

class TestLIUMSTM(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    CAMERON_SAMPLE = [
        'JamesCameron_2010 1 inter_segment_gap 0 16.75 <o,,unknown> ignore_time_segment_in_scoring',
        'JamesCameron_2010 1 JamesCameron 16.75 27.96 <o,f0,male> i grew up on a steady diet of science fiction in high school i i took a bus to school an hour eac    h way every day and i was always absorbed in a book',
        'JamesCameron_2010 1 JamesCameron 27.96 41.81 <o,f0,male> science fiction book which took my mind to other worlds and satisfied this in in a in a narrative     form this insatiable sense of curiosity that i had and and',
    ]
    CAMERON_EXPECTED = [
        'i grew up on a steady diet of science fiction in high school i i took a bus to school an hour eac    h way every day and i was always absorbed in a book',
        'science fiction book which took my mind to other worlds and satisfied this in in a in a narrative     form this insatiable sense of curiosity that i had and and'
    ]
    def test_stm_parser(self):
        parsed = list( stm.STMParser( self.CAMERON_SAMPLE ))
        transcripts = [x.transcript for x in parsed]
        assert transcripts == self.CAMERON_EXPECTED, transcripts


if __name__ == '__main__':
    unittest.main()
