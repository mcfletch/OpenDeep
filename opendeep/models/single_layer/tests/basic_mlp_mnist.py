from __future__ import print_function

from theano.tensor import matrix

from opendeep.models.single_layer.basic import Dense, Softmax
from opendeep.models.container import Prototype
from opendeep.optimization.loss import Neg_LL

# import the dataset and optimizer to use
from opendeep.data.standard_datasets.image.mnist import MNIST
from opendeep.optimization.adadelta import AdaDelta


if __name__ == '__main__':
    # set up the logging environment to display outputs (optional)
    # although this is recommended over print statements everywhere
    from opendeep.log import config_root_logger
    config_root_logger()

    # grab the MNIST dataset
    mnist = MNIST()
    # create the basic layer
    layer1 = Dense(inputs=((None, 28*28), matrix("x")),
                   outputs=1000,
                   activation='relu')
    # create the softmax classifier
    layer2 = Softmax(inputs=((None, 1000), layer1.get_outputs()),
                     outputs=10,
                     out_as_probs=False)
    # create the mlp from the two layers
    mlp = Prototype(layers=[layer1, layer2])
    # define the loss function
    loss = Neg_LL(inputs=mlp.get_outputs(), targets=matrix("y", dtype="int32"), one_hot=False)

    # make an optimizer to train it (AdaDelta is a good default)
    # optimizer = AdaDelta(model=mlp, dataset=mnist, n_epoch=20)
    optimizer = AdaDelta(dataset=mnist, epochs=20)
    # perform training!
    # optimizer.train()
    mlp.train(optimizer)

    # test it on some images!
    test_data, test_labels = mnist.test_inputs, mnist.test_targets
    test_data = test_data[:25]
    test_labels = test_labels[:25]
    # use the run function!
    preds = mlp.run(test_data)
    print('-------')
    print(preds)
    print(test_labels.astype('int32'))
    print()
    print()
    del mnist
    del mlp
    del optimizer
