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
import logging, subprocess, os, random
log = logging.getLogger(__name__)
from opendeep.data.standard_datasets.tedlium import stm, sph

class Speech( object ):
    """Binds together audio and transcription for a given speech"""
    def __init__(self, sph_file, stm_file=None, window_duration=0.01 ):
        """Initialize with a pointer to the two data-files on disk"""
        self.sph_file = sph.SPHFile(sph_file,window_duration=window_duration)
        if stm_file is None:
            base = os.path.basename( sph_file )
            stm_file = os.path.join(
                os.path.dirname(sph_file),
                '..',
                'stm',
                os.path.splitext( base )[0] + '.stm'
            )
        self.stm_file = stm_file
    def __iter__(self):
        self.stm = stm.STMParser( open(self.stm_file,'rb') )
        for segment in self.stm:
            segment.speech = self
            segment.audio_data = self.sph_file.audio_segment( segment.start, segment.stop )
            yield segment
    def __str__(self):
        return '%s(%s)'%(self.__class__.__name__,self.sph_file.filename)

    def playing_pipe(self):
        """Create a pipe to play audio in our format"""
        pipe_command = [
            'gst-launch',
                'fdsrc',
                    'fd=0',
                '!',
                    'audio/x-raw-int,width=16,channels=1,format=%(gst_format)s,rate=%(sample_rate)s'%self.sph_file.format,
                '!', 'alsasink'
        ]
        log.info("Starting gstreamer with: %s", " ".join(pipe_command))
        pipe = subprocess.Popen(pipe_command,stdin=subprocess.PIPE)
        return pipe

    def play_segment(self,pipe,segment):
        """Play the given segment on the pipe"""
        log.info( 'Transcript: %s', segment.transcript)
        if self.sph_file.needs_byteswap:
            data = segment.audio_data.byteswap()
        else:
            data = segment.audio_data
        pipe.stdin.write(data.tobytes()) # yes, stupid, should do a direct binary write

    def play(self):
        """Use gstreamer-utils to play our audio to alsa while logging transcripts

        This is intended primarily to allow you to hear what
        the NN is getting

        """
        log.info("Playing file %s with format %s",self.sph_file.filename,self.sph_file.format)
        pipe = self.playing_pipe()
        for segment in self:
            self.play_segment(pipe,segment)

def random_walk( directory ):
    """Do a random walk of directory loading fragments of speeches"""
    import os
    count = 0
    filenames = []
    for path,dirs,files in os.walk(directory):
        sphs = [x for x in files if x.lower().endswith('.sph')]
        filenames.extend([
            os.path.join(path,f)
            for f in sphs
        ])
    pipe = None
    while True:
        speech = Speech( random.choice(filenames) )
        log.info("Speech: %s",speech)
        if pipe is None:
            pipe = speech.playing_pipe()
        segments = list(speech)
        segment = random.choice(segments)
        log.info("  Segment @%ss",segment.start)
        #speech.play_segment(pipe,segment)

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    random_walk( sys.argv[1] )
