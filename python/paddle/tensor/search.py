#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function
import numpy as np
import warnings
import six
import os
import inspect
from ..fluid.layer_helper import LayerHelper
from ..fluid.data_feeder import check_variable_and_dtype, check_type, check_dtype
from ..fluid.initializer import Normal, Constant, NumpyArrayInitializer
from ..fluid.framework import Variable, OpProtoHolder, in_dygraph_mode, dygraph_only, _dygraph_tracer, default_main_program
from ..fluid import dygraph_utils
from ..fluid.param_attr import ParamAttr
from ..fluid import unique_name
from ..fluid import core, layers

# TODO: define searching & indexing functions of a tensor  
__all__ = [
    'argmax',
    #            'argmin',
    #            'argsort',
    #            'has_inf',
    #            'has_nan',
    #            'masked_select',
    #            'topk',
    'where',
    #            'index_select',
    #            'nonzero',
    'sort',
    'index_sample'
]

from paddle.common_ops_import import *


def argmax(input, axis=None, dtype=None, out=None, keepdims=False, name=None):
    """
    This OP computes the indices of the max elements of the input tensor's
    element along the provided axis.

    Args:
        input(Variable): An input N-D Tensor with type float32, float64, int16,
            int32, int64, uint8.
        axis(int, optional): Axis to compute indices along. The effective range
            is [-R, R), where R is Rank(input). when axis<0, it works the same way
            as axis+R. Default is None, it will use the last dim to select indices of max value.
        dtype(np.dtype|core.VarDesc.VarType|str): Data type of the output tensor which can
                    be int32, int64. The default value is None, and it will
                    return the int64 indices.
        out(Variable, optional): Optional output which can be any created 
            Variable that meets the requirements to store the result of operation.
            if out is None, a new Varibale will be create to store the result. Defalut is None.
        keepdims(bool, optional): Keep the axis that do the select max.
        name(str, optional): The name of output variable, normally there is no need for user to set this this property. 
            Default value is None, the framework set the name of output variable.  


    Returns:
        Variable: A Tensor with data type int64.

    Examples:
        .. code-block:: python

            import paddle
            import paddle.fluid as fluid
            import numpy as np

            in1 = np.array([[[5,8,9,5],
                            [0,0,1,7],
                            [6,9,2,4]],
                            [[5,2,4,2],
                            [4,7,7,9],
                            [1,7,0,6]]])
            with fluid.dygraph.guard():
                x = fluid.dygraph.to_variable(in1)
                out1 = paddle.argmax(input=x, axis=-1)
                out2 = paddle.argmax(input=x, axis=0)
                out3 = paddle.argmax(input=x, axis=1)
                out4 = paddle.argmax(input=x, axis=2)
                out5 = paddle.argmax(input=x, axis=2, keepdims=True)
                print(out1.numpy())
                # [[2 3 1]
                #  [0 3 1]]
                print(out2.numpy())
                # [[0 0 0 0]
                #  [1 1 1 1]
                #  [0 0 0 1]]
                print(out3.numpy())
                # [[2 2 0 1]
                #  [0 1 1 1]]
                print(out4.numpy())
                # [[2 3 1]
                #  [0 3 1]]
                print(out5.numpy())
                #array([[[2],
                #        [3],
                #        [1]],
                #       [[0],
                #        [3],
                #        [1]]])
    """
    helper = LayerHelper("arg_max", **locals())
    var_dtype = None
    attrs = {}
    if dtype is not None:
        check_dtype(dtype, 'create data type', ['int32', 'int64'], 'arg_max')
        var_dtype = convert_np_dtype_to_dtype_(dtype)
        attrs["dtype"] = var_dtype
    else:
        var_dtype = VarDesc.VarType.INT64
    if out is None:
        out = helper.create_variable_for_type_inference(var_dtype)
    if axis is None:
        axis = -1
    attrs['keepdims'] = keepdims
    attrs['axis'] = axis
    helper.append_op(
        type='arg_max',
        inputs={'X': input},
        outputs={'Out': [out]},
        attrs=attrs)
    out.stop_gradient = True
    return out


def sort(input, axis=-1, descending=False, out=None, name=None):
    """
    This OP sorts the input along the given axis, and returns sorted output
    data Varibale and its corresponding index Variable with the same shape as
    :attr:`input`.

    **NOTICE**: The Variable in the output of this OP has gradient. You could\
        set Variable :attr:`stop_gradient`.
    Args:
        input(Variable): An input N-D Tensor with type float32, float64, int16,
            int32, int64, uint8.
        axis(int, optional): Axis to compute indices along. The effective range
            is [-R, R), where R is Rank(x). when axis<0, it works the same way
            as axis+R. Default is 0.
        descending(bool, optional) : Descending is a flag, if set to true,
            algorithm will sort by descending order, else sort by
            ascending order. Default is false.
        out(Variable, optional): The default value is None. Optional output 
            which can be any created Variable that meets the requirements to
            store the result of operation. if out is None, a new Varibale will
            be create to store the result.
        name(str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.
    Returns:
        tuple: A tuple of sorted data Variable(with the same shape and data
        type as input) and the sorted indices(with the same shape as input's
        and with data type int64).
    Examples:
        .. code-block:: python
            import paddle
            import paddle.fluid as fluid
            import numpy as np
            in1 = np.array([[[5,8,9,5],
                            [0,0,1,7],
                            [6,9,2,4]],
                            [[5,2,4,2],
                            [4,7,7,9],
                            [1,7,0,6]]]).astype(np.float32)
            with fluid.dygraph.guard():
                x = fluid.dygraph.to_variable(in1)
                out1 = paddle.sort(input=x, axis=-1)
                out2 = paddle.sort(input=x, axis=0)
                out3 = paddle.sort(input=x, axis=1)
                print(out1[0].numpy())
                # [[[5. 5. 8. 9.]
                #   [0. 0. 1. 7.]
                #   [2. 4. 6. 9.]]
                #  [[2. 2. 4. 5.]
                #   [4. 7. 7. 9.]
                #   [0. 1. 6. 7.]]]
                print(out1[1].numpy())
                # [[[0 3 1 2]
                #   [0 1 2 3]
                #   [2 3 0 1]]
                #  [[1 3 2 0]
                #   [0 1 2 3]
                #   [2 0 3 1]]]
                print(out2[0].numpy())
                # [[[5. 2. 4. 2.]
                #   [0. 0. 1. 7.]
                #   [1. 7. 0. 4.]]
                #  [[5. 8. 9. 5.]
                #   [4. 7. 7. 9.]
                #   [6. 9. 2. 6.]]]
                print(out3[0].numpy())
                # [[[0. 0. 1. 4.]
                #   [5. 8. 2. 5.]
                #   [6. 9. 9. 7.]]
                #  [[1. 2. 0. 2.]
                #   [4. 7. 4. 6.]
                #   [5. 7. 7. 9.]]]
    """
    helper = LayerHelper("sort", **locals())
    if out is None:
        out = helper.create_variable_for_type_inference(
            dtype=input.dtype, stop_gradient=False)
    ids = helper.create_variable_for_type_inference(
        VarDesc.VarType.INT64, stop_gradient=True)
    helper.append_op(
        type='argsort',
        inputs={'X': input},
        outputs={'Out': out,
                 'Indices': ids},
        attrs={'axis': axis,
               'descending': descending})
    return out, ids


def where(Condition, X, Y):
    """
    Return a tensor of elements selected from either $X$ or $Y$, depending on $Condition$.
    Args:
        Condition(Variable): A bool tensor with rank at least 1, the data type is bool.
        X(Variable): X is a Tensor Variable.
        Y(Variable): Y is a Tensor Variable.
    Returns:
        out : The tensor. 
    Examples:
        .. code-block:: python

          import numpy as np
          import paddle as paddle
          import paddle.fluid as fluid

          with fluid.dygraph.guard():
              x_i = np.array([0.9383, 0.1983, 3.2, 1.2]).astype("float64")
              y_i = np.array([1.0, 1.0, 1.0, 1.0]).astype("float64")
              x = fluid.dygraph.to_variable(x_i)
              y = fluid.dygraph.to_variable(y_i)
              out = paddle.where(x>1, x, y)
              print(out.numpy())
              #out: [1.0, 1.0, 3.2, 1.2]
    """
    if not in_dygraph_mode():
        check_variable_and_dtype(Condition, 'Condition', ['bool'], 'where')
        check_variable_and_dtype(
            X, 'X', ['float32', 'float64', 'int32', 'int64'], 'where')
        check_variable_and_dtype(
            Y, 'Y', ['float32', 'float64', 'int32', 'int64'], 'where')

    X_shape = list(X.shape)
    Y_shape = list(Y.shape)
    if X_shape == Y_shape:
        if in_dygraph_mode():
            return core.ops.where(Condition, X, Y)
        else:
            helper = LayerHelper("where", **locals())
            dtype = helper.input_dtype()
            out = helper.create_variable_for_type_inference(dtype)

            helper.append_op(
                type='where',
                inputs={'Condition': Condition,
                        'X': X,
                        'Y': Y},
                outputs={'Out': [out]})
            return out
    else:
        cond_int = layers.cast(Condition, X.dtype)
        cond_not_int = layers.cast(layers.logical_not(Condition), X.dtype)
        out1 = layers.elementwise_mul(X, cond_int)
        out2 = layers.elementwise_mul(Y, cond_not_int)
        out = layers.elementwise_add(out1, out2)
        return out


def index_sample(x, index):
    """
    **IndexSample Layer**

    IndexSample OP returns the element of the specified location of X, 
    and the location is specified by Index. 

    .. code-block:: text


                Given:

                X = [[1, 2, 3, 4, 5],
                     [6, 7, 8, 9, 10]]

                Index = [[0, 1, 3],
                         [0, 2, 4]]

                Then:

                Out = [[1, 2, 4],
                       [6, 8, 10]]

    Args:
        x (Variable): The source input tensor with 2-D shape. Supported data type is 
            int32, int64, float32, float64.
        index (Variable): The index input tensor with 2-D shape, first dimension should be same with X. 
            Data type is int32 or int64.

    Returns:
        output (Variable): The output is a tensor with the same shape as index.

    Examples:

        .. code-block:: python

            import paddle
            import paddle.fluid as fluid
            import numpy as np

            # create x value
            x_shape = (2, 5)
            x_type = "float64"
            x_np = np.random.random(x_shape).astype(x_type)

            # create index value
            index_shape = (2, 3)
            index_type = "int32"
            index_np = np.random.randint(low=0, 
                                         high=x_shape[1],
                                         size=index_shape).astype(index_type)

            x = fluid.data(name='x', shape=[-1, 5], dtype='float64')
            index = fluid.data(name='index', shape=[-1, 3], dtype='int32')
            output = paddle.index_sample(x=x, index=index)

    """
    helper = LayerHelper("index_sample", **locals())
    check_variable_and_dtype(x, 'x', ['float32', 'float64', 'int32', 'int64'],
                             'paddle.tensor.search.index_sample')
    check_variable_and_dtype(index, 'index', ['int32', 'int64'],
                             'paddle.tensor.search.index_sample')
    out = helper.create_variable_for_type_inference(dtype=x.dtype)

    helper.append_op(
        type='index_sample',
        inputs={'X': x,
                'Index': index},
        outputs={'Out': out})
    return out
