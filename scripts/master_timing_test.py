import sys
import numpy as np
import chopperhack19.mock_obs
from chopperhack19.mock_obs.tests import random_weighted_points
from chopperhack19.mock_obs.tests.generate_test_data import (
    DEFAULT_RBINS_SQUARED)
from time import time

if len(sys.argv) == 2:
    func_str = sys.argv[1]
else:
    func_str = 'count_weighted_pairs_3d_cpu'

func = getattr(chopperhack19.mock_obs, func_str)
if func is None:
    raise ImportError('could not import %s' % func_str)

print('func_str:', func_str)
print('func:', func)

Lbox = 1000.
result = np.zeros_like(DEFAULT_RBINS_SQUARED)

n1 = 128
n2 = 128
x1, y1, z1, w1 = random_weighted_points(n1, Lbox, 0)
x2, y2, z2, w2 = random_weighted_points(n2, Lbox, 1)

func(
    x1, y1, z1, w1, x2, y2, z2, w2, DEFAULT_RBINS_SQUARED, result)

n1 = 50013
n2 = 50013
x1, y1, z1, w1 = random_weighted_points(n1, Lbox, 0)
x2, y2, z2, w2 = random_weighted_points(n2, Lbox, 1)

if 'cuda' in func_str:
    from numba import cuda

    d_x1 = cuda.to_device(x1)
    d_y1 = cuda.to_device(y1)
    d_z1 = cuda.to_device(z1)
    d_w1 = cuda.to_device(w1)

    d_x2 = cuda.to_device(x2)
    d_y2 = cuda.to_device(y2)
    d_z2 = cuda.to_device(z2)
    d_w2 = cuda.to_device(w2)

    d_rbins_squared = cuda.to_device(DEFAULT_RBINS_SQUARED)
    d_result = cuda.device_array_like(result)

    threads_per_warp = 32
    warps_per_block = 4
    threads_per_block = warps_per_block*threads_per_warp
    blocks_per_grid = 32

    start = time()
    func[blocks_per_grid, threads_per_block](
        d_x1, d_y1, d_z1, d_w1, d_x2, d_y2, d_z2, d_w2,
        d_rbins_squared, d_result)
    results_host = d_result.copy_to_host()
    end = time()

else:
    d_x1 = x1
    d_y1 = y1
    d_z1 = z1
    d_w1 = w1

    d_x2 = x2
    d_y2 = y2
    d_z2 = z2
    d_w2 = w2

    d_rbins_squared = DEFAULT_RBINS_SQUARED
    d_result = result

    start = time()
    func(
        d_x1, d_y1, d_z1, d_w1, d_x2, d_y2, d_z2, d_w2,
        d_rbins_squared, d_result)
    end = time()
    runtime = end-start

print('time:', runtime)
