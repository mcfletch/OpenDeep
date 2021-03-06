from __future__ import print_function
import numpy
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from opendeep.models.multi_layer.rnn_gsn import RNN_GSN
from opendeep.data.standard_datasets.tedlium import dataset as tedlium
from opendeep.data.standard_datasets.codegolfyesno import dataset as codegolf
from opendeep.optimization.adadelta import AdaDelta
from opendeep.utils.image import tile_raster_images
from opendeep.utils.misc import closest_to_square_factors
from opendeep.monitor.monitor import Monitor
from opendeep.monitor.plot import Plot
import PIL.Image as Image
try:
    import pylab
    has_pylab = True
except ImportError:
    print("pylab isn't available.")
    print("It can be installed with 'pip install -q pylab'")
    has_pylab = False

import logging
from opendeep.log.logger import config_root_logger

log = logging.getLogger(__name__)


def run_audio(dataset):
    log.info("Creating RNN-GSN for dataset %s!", dataset)

    outdir = "outputs/rnngsn/%s/" % dataset

    # grab the dataset
    if dataset == 'tedlium':
        dataset = tedlium.TEDLIUMDataset(max_speeches=3)
        extra_args = {
        }
    elif dataset == 'codegolf':
        dataset = codegolf.CodeGolfDataset()
        extra_args = {
        }
    else:
        raise ValueError("dataset %s not recognized." % dataset)

    rng = numpy.random.RandomState(1234)
    mrg = RandomStreams(rng.randint(2 ** 30))
    assert dataset.window_size == 256, dataset.window_size
    
    rnngsn = RNN_GSN(layers=2,
                     walkbacks=4,
                     input_size=dataset.window_size,
                     image_height = 1,
                     image_width = 256,
                     hidden_size=128,
                     rnn_hidden_size=128,
                     weights_init='gaussian',
                     weights_std=0.01,
                     rnn_weights_init='identity',
                     rnn_hidden_activation='relu',
                     rnn_weights_std=0.0001,
                     mrg=mrg,
                     outdir=outdir, **extra_args)

    # make an optimizer to train it
    optimizer = AdaDelta(model=rnngsn,
                         dataset=dataset,
                         epochs=200,
                         batch_size=128,
                         min_batch_size=2,
                         learning_rate=1e-6,
                         save_freq=1,
                         stop_patience=100)

    ll = Monitor('crossentropy', rnngsn.get_monitors()['noisy_recon_cost'],test=True)
    mse = Monitor('frame-error', rnngsn.get_monitors()['mse'],train=True,test=True,valid=True)
    plot = Plot(
        bokeh_doc_name='rnngsn_tedlium_%s'%dataset, monitor_channels=[ll,mse],open_browser=True
    )

    # perform training!
    optimizer.train(plot=plot)
    
    # use the generate function!
    generated, _ = rnngsn.generate(initial=None, n_steps=200)

    # Construct image from the weight matrix
    image = Image.fromarray(
        tile_raster_images(
            X=rnngsn.weights_list[0].get_value(borrow=True).T,
            img_shape=closest_to_square_factors(rnngsn.input_size),
            tile_shape=closest_to_square_factors(rnngsn.hidden_size),
            tile_spacing=(1, 1)
        )
    )
    image.save(outdir + 'rnngsn_%s_weights.png'%(dataset,))

    log.debug("done!")
    del rnngsn
    del optimizer

    if has_pylab:
        pylab.show()

if __name__ == '__main__':
    config_root_logger()
    import sys
    if not sys.argv[1:]:
        dataset = 'tedlium'
    else:
        dataset = sys.argv[1]
    run_audio(dataset)
