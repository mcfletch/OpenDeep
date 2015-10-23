"""
These functions are used as the objectives (costs) to minimize during training of deep networks.
You should be careful to use the appropriate cost function for the type of input and output of the network.

EVERY COST FUNCTION SHOULD INCLUDE AND OUTPUT AND TARGET PARAMETER. Extra parameters can be included and named
whatever you like.
"""
# standard libraries
import logging
# third party libraries
import theano.tensor as T
import theano.compat.six as six
import numpy

log = logging.getLogger(__name__)

def binary_crossentropy(output, target):
    """
    Computes the mean binary cross-entropy between a target and an output, across all dimensions
    (both the feature and example dimensions).

    Parameters
    ----------
    output : tensor
        Symbolic Tensor (or compatible) that is your output from the network. (Comes from model).
    target : tensor
        Symbolic Tensor (or compatible) that is the target truth you want to compare the output against.
        (Comes from model).

    Returns
    -------
    number
        The mean of the binary cross-entropy tensor, where binary cross-entropy is applied element-wise:
        crossentropy(target,output) = -(target*log(output) + (1 - target)*(log(1 - output)))

    .. note::
        Use this cost for binary outputs, like MNIST.

    """
    return T.mean(T.nnet.binary_crossentropy(output, target))
    # The following definition came from the Conditional_nade project
    # L = - T.mean(target * T.log(output) +
    #              (1 - target) * T.log(1 - output), axis=1)
    # cost = T.mean(L)
    # return cost

def categorical_crossentropy(output, target):
    """
    This is the mean multinomial negative log-loss.
    From Theano:
    Return the mean cross-entropy between an approximating distribution and a true distribution, across all dimensions.
    The cross entropy between two probability distributions measures the average number of bits needed to identify an
    event from a set of possibilities, if a coding scheme is used based on a given probability distribution q, rather
    than the "true" distribution p.
    Mathematically, this function computes H(p,q) = - \sum_x p(x) \log(q(x)), where p=target_distribution and
    q=coding_distribution.

    Parameters
    ----------
    output : tensor
        Symbolic 2D tensor (or compatible) where each row represents a distribution.
    target : tensor
        Symbolic 2D tensor *or* symbolic vector of ints. In the case of an integer vector argument,
        each element represents the position of the '1' in a 1-of-N encoding (aka 'one-hot' encoding)

    Returns
    -------
    number
        The mean of the cross-entropy tensor.
    """
    return T.mean(T.nnet.categorical_crossentropy(output, target))

def mse(output, target, mean_over_second=True):
    """
    This is the Mean Square Error (MSE) across all dimensions, or per multibatch row (depending on mean_over_second).

    Parameters
    ----------
    output : tensor
        The symbolic tensor (or compatible) output from the network. (Comes from model).
    target : tensor
        The symbolic tensor (or compatible) target truth to compare the output against. (Comes from data).
    mean_over_second : bool
        Boolean whether or not to take the mean across all dimensions (True) or just the
        feature dimensions (False)

    Returns
    -------
    number
        The appropriate mean square error.
    """
    # The following definition came from the Conditional_nade project
    if mean_over_second:
        cost = T.mean(T.sqr(target - output))
    else:
        cost = T.mean(T.sqr(target - output).sum(axis=1))
    return cost

def isotropic_gaussian_LL(output, target, std_estimated):
    """
    This takes the negative log-likelihood of an isotropic Gaussian with estimated mean and standard deviation.
    Useful for continuous-valued costs.

    Parameters
    ----------
    output : tensor
        The symbolic tensor (or compatible) representing the means of the distribution estimated.
        In the case of Generative Stochastic Networks, for example, this would be the final reconstructed output x'.
    std_estimated : tensor
        The estimated standard deviation (sigma).
    target : tensor
        The symbolic tensor (or compatible) target truth to compare the means_estimated against.

    Returns
    -------
    number
        The negative log-likelihood cost.

    .. note::
        Use this cost, for example, on Generative Stochastic Networks when the input/output is continuous
        (alternative to mse cost).

    """
    # The following definition came from the Conditional_nade project
    #the loglikelihood of isotropic Gaussian with
    # estimated mean and std
    A = -((target - output)**2) / (2*(std_estimated**2))
    B = -T.log(std_estimated * T.sqrt(2*numpy.pi))
    LL = (A + B).sum(axis=1).mean()
    return -LL
    # Example from GSN:
    # this_cost = isotropic_gaussian_LL(
    #     output=reconstruction,
    #     std_estimated=self.layers[0].sigma,
    #     target=self.inputs)

def zero_one(output, target):
    """
    This defines the zero-one loss function, where the loss is equal to the number of incorrect estimations.

    Parameters
    ----------
    output : tensor
        The estimated variable. (Output from computation).
    target : tensor
        The ground truth variable. (Comes from data).

    Returns
    -------
    number
        The appropriate zero-one loss between output and target.
    """
    return T.sum(T.neq(output, target))

def negative_log_likelihood(output, target, one_hot=True):
    """
    Return the mean of the negative log-likelihood of the prediction
    of this model under a given target distribution.

    Notes
    -----
    We use the mean instead of the sum so that the learning rate is less dependent on the batch size.
    TARGETS MUST BE ONE-HOT ENCODED (a vector with 0's except 1 for the correct label).

    Parameters
    ----------
    output : tensor
        The output probability of target given input P(Y|X).
    target : tensor
        The correct target labels Y.
    one_hot : bool
        Whether the label targets Y are encoded as a one-hot vector or as the int class label.
        If it is not one-hot, needs to be 2-dimensional.

    Note:
    """
    p_y_given_x = output
    y = target
    # y.shape[0] is (symbolically) the number of examples (call it n) in the minibatch.
    # T.arange(y.shape[0]) is a symbolic vector which will contain [0,1,2,... n-1]
    # T.log(self.p_y_given_x) is a matrix of Log-Probabilities (call it LP) with one row per example and
    # one column per class
    # LP[T.arange(y.shape[0]),y] is a vector v containing [LP[0,y[0]], LP[1,y[1]], LP[2,y[2]], ..., LP[n-1,y[n-1]]] and
    # T.mean(LP[T.arange(y.shape[0]),y]) is the mean (across minibatch examples) of the elements in v,
    # i.e. the mean log-likelihood across the minibatch.

    if one_hot:
        # if one_hot, labels y act as a mask over p_y_given_x
        assert y.ndim == p_y_given_x.ndim
        return -T.mean(T.log(p_y_given_x)*y)
    else:
        assert p_y_given_x.ndim == 2
        assert y.ndim == 1
        return -T.mean(T.log(p_y_given_x)[T.arange(y.shape[0]), T.cast(y, 'int32')])


########### keep cost functions above this line, and add them to the dictionary below ####################
_functions = {
    'binary_crossentropy': binary_crossentropy,
    'categorical_crossentropy': categorical_crossentropy,
    'mse': mse,
    'isotropic_gaussian': isotropic_gaussian_LL,
    'zero_one': zero_one,
    'nll': negative_log_likelihood
}

def get_cost_function(name):
    """
    This helper method returns the appropriate cost function given a string name. It looks up the appropriate
    function from the internal _functions dictionary.

    Parameters
    ----------
    name : str or Callable
        String representation of the cost function you want (or already a Callable function).

    Returns
    -------
    function
        The appropriate cost function.

    Raises
    ------
    NotImplementedError
        If the function can't be found in the dictionary.
    """
    # if the name is callable, return the function
    if callable(name):
        return name
    # otherwise if it is a string name
    elif isinstance(name, six.string_types):
        # standardize the input to be lowercase
        name = name.lower()
        # grab the appropriate activation function from the dictionary of functions
        func = _functions.get(name)
        # if it couldn't find the function (key didn't exist), raise a NotImplementedError
        if func is None:
            log.error("Did not recognize cost function %s! Please use one of: ", str(name), str(_functions.keys()))
            raise NotImplementedError(
                "Did not recognize cost function {0!s}! Please use one of: {1!s}".format(name, _functions.keys())
            )
        # return the found function
        return func
    # otherwise we don't know what to do.
    else:
        log.error("Cost function not implemented for %s with type %s", str(name), str(type(name)))
        raise NotImplementedError("Cost function not implemented for %s with type %s", str(name), str(type(name)))