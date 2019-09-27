import numpy as np
import click

import chopperhack19.mock_obs
from chopperhack19.mock_obs.tests import random_weighted_points
from chopperhack19.mock_obs.tests.generate_test_data import (
    DEFAULT_RBINS_SQUARED)
from time import time


@click.command()
@click.option('--func', default='count_weighted_pairs_3d_cuda',
              help='the function to run')
@click.option('--blocks', default=512)
@click.option('--threads', default=512)
@click.option('--npoints', default=200013)
def _main(func, blocks, threads, npoints):

    func_str = func
    func = getattr(chopperhack19.mock_obs, func)
    if func is None:
        raise ImportError('could not import %s' % func_str)

    print('func_str:', func_str)
    print('func:', func)
    print('npoints:', npoints)
    if 'cuda' in func_str:
        from numba import cuda

        print('blocks:', blocks)
        print('threads:', threads)

    Lbox = 1000.
    result = np.zeros_like(DEFAULT_RBINS_SQUARED)[:-1]
    result = result.astype(np.float32)

    n1 = npoints
    n2 = npoints
    x1, y1, z1, w1 = random_weighted_points(n1, Lbox, 0)
    x2, y2, z2, w2 = random_weighted_points(n2, Lbox, 1)
    if 'cuda2d' in func_str:
        assert blocks * threads == n1
        assert blocks * threads == n2
        blocks = (blocks, blocks)
        threads = (threads, threads)

    d_x1 = cuda.to_device(x1.astype(np.float32))
    d_y1 = cuda.to_device(y1.astype(np.float32))
    d_z1 = cuda.to_device(z1.astype(np.float32))
    d_w1 = cuda.to_device(w1.astype(np.float32))

    d_x2 = cuda.to_device(x2.astype(np.float32))
    d_y2 = cuda.to_device(y2.astype(np.float32))
    d_z2 = cuda.to_device(z2.astype(np.float32))
    d_w2 = cuda.to_device(w2.astype(np.float32))

    d_rbins_squared = cuda.to_device(
        DEFAULT_RBINS_SQUARED.astype(np.float32))
    d_result = cuda.device_array_like(result.astype(np.float64))

    # once for compile
    func[blocks, threads](
        d_x1, d_y1, d_z1, d_w1, d_x2, d_y2, d_z2, d_w2,
        d_rbins_squared, d_result)
    results_host = d_result.copy_to_host()

    # thrice to time
    start = time()
    for _ in range(3):
        func[blocks, threads](
            d_x1, d_y1, d_z1, d_w1, d_x2, d_y2, d_z2, d_w2,
            d_rbins_squared, d_result)
        results_host = d_result.copy_to_host()
    end = time()
    assert np.all(np.isfinite(results_host))
    runtime = (end-start)/3

    results_host /= 4

    # run corrfunc to check
    result_test = np.zeros_like(result)
    chopperhack19.mock_obs.count_weighted_pairs_3d_cpu_corrfunc(
        x1, y1, z1, w1, x2, y2, z2, w2, DEFAULT_RBINS_SQUARED, result_test)
    correct = np.allclose(result_test, results_host, atol=0, rtol=2e-7)

    print('time:', runtime)
    print('correct (only valid for cumulative counts):', correct)
    if not correct:
        print('result           :', results_host)
        print('result (corrfunc):', result_test)


if __name__ == '__main__':
    _main()