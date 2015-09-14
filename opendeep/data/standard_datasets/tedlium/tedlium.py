"""Data-format Loader for the TED LIUM Data-set

These are transcribed audio files, with transcriptions
in "STM" format and audio in NIST SPH format. The 
Loader here attempts to make them usable as in chunks
so that you can train individual "utterances" from a 
speech.

TED LIUM requires registration, and may not be redistributed,
so the data-files here have to be downloaded by each person
from the `LIUM site`_.

.. _`LIUM site`: http://www-lium.univ-lemans.fr/en/content/form-downloads?equipe=parole&projet=tedlium&fichier=TEDLIUM_release2.tar.gz
    
"""
import logging, subprocess, os
log = logging.getLogger(__name__)
from opendeep.data.standard_datasets.tedlium import stm, sph

class Speech( object ):
    """Binds together audio and transcription for a given speech"""
    def __init__(self, sph_file, stm_file=None ):
        """Initialize with a pointer to the two data-files on disk"""
        self.sph_file = sph_file
        if stm_file is None:
            base = os.path.basename( sph_file )
            stm_file = os.path.join(
                os.path.dirname(sph_file),
                '..',
                'stm',
                os.path.splitext( base )[0] + '.stm'
            )
        self.stm_file = stm_file
        self._format = None
    @property
    def format(self):
        if self._format is None:
            with open( self.sph_file, 'rb') as fh:
                self._format = sph.parse_sph_header( fh )
        return self._format
    def __iter__(self):
        format = self.format
        sample_rate = format['sample_rate']
        with open( self.sph_file, 'rb') as fh:
            data = sph.load_audio_data( fh, format, force_native=True )
        self.stm = stm.STMParser( open(self.stm_file,'rb') )
        for segment in self.stm:
            start,stop = int(segment.start*sample_rate),int(segment.stop*sample_rate)+1
            segment.audio_data = data[start:stop]
            yield segment
    
    def playing_pipe(self):
        """Create a pipe to play audio in our format"""
        pipe = subprocess.Popen([
            'gst-launch',
                'fdsrc',
                    'fd=0',
                '!',
                    'audio/x-raw-int,width=16,channels=1,format=%(gst_format)s,rate=%(sample_rate)s'%self.format,
                '!', 'alsasink'
        ],stdin=subprocess.PIPE)
        return pipe
    
    def play(self):
        """Use gstreamer-utils to play our audio to alsa while logging transcripts
        
        This is intended primarily to allow you to hear what
        the NN is getting
        
        """
        pipe = self.playing_pipe()
        for segment in self:
            log.info( 'Transcript: %s', segment.transcript)
            pipe.stdin.write(segment.audio_data.tostring()) # yes, stupid, should do a direct binary write

def play_speech( filename ):
    s = Speech( filename )
    s.play()

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    play_speech( sys.argv[1] )
