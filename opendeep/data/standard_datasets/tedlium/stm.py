"""Loader for .sph files such as found in TEDLium dataset"""
from __future__ import print_function
import logging
log = logging.getLogger(__name__)

class STMParser( object ):
    """Read an iterable of an STM data-file (transcript) and yield segments
    
    Notes:
    
        Assumes that the text is actually utf-8 encoded, which hasn't been confirmed
        
        Is just written by inspecting the file, not by looking up a spec
    
    Usage::
    
        for segment in STMParser( open( 'path-to-stm.stm' ) ):
            utterance = audio[
                int(segment.start*(samples_per_second)):int(segment.stop*(samples_per_second))
            ]
            yield segment, utterance
    
    """
    def __init__(self, iterable ):
        self.iterable = iterable
    IGNORE_SPEAKERS = set([
        'inter_segment_gap',
    ])
    IGNORE_TRANSCRIPT = set([
        'ignore_time_segment_in_scoring',
    ])
    def __iter__(self):
        """Iteratively parse every line of the source iterable"""
        for i,line in enumerate(self.iterable):
            try:
                line = line.strip()
                title,num,speaker,start,stop,speakermeta,transcript = line.split(None,6)
                start,stop = float(start),float(stop)
                if (
                    speaker in self.IGNORE_SPEAKERS
                    or 
                    transcript in self.IGNORE_TRANSCRIPT
                ):
                    continue
                yield STMSegment( self,start,stop,transcript.decode('utf-8'),title,num,speaker,speakermeta )
            except Exception as err:
                log.error(
                    "Syntax error on line %s of %s: %s\n%s", i+1, self.iterable, err, line,
                )

class STMSegment( object ):
    """Segment spec of an audio transcript with associated metadata"""
    def __init__(self, reader, start, stop, transcript, title=None,num=None,speaker=None,speakermeta=None):
        self.reader,self.start,self.stop,self.transcript,self.title,self.num,self.speaker,self.speakermeta = (
            reader,start,stop,transcript,title,num,speaker,speakermeta
        )
        self.audio_data = None
    def __unicode__(self):
        return u'%s %s:%s %s'%( 
            self.reader, self.start,self.stop, self.transcript
        )

def _parse_all_stms( filepath ):
    """Trivial "does it crash" manual test operation
    
    This just confirms that all of the TED LIUM corpus can
    be parsed. It doesn't necessarily mean that the parsing 
    is *correct*
    """
    import os
    for path,dirs,files in os.walk(filepath):
        stms = [x for x in files if x.lower().endswith('.stm')]
        for stm in stms:
            source = open(os.path.join(path,stm))
            content = list(STMParser(source))
            for segment in content:
                print(segment.transcript.encode('utf-8'))

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    _parse_all_stms( sys.argv[1] )
