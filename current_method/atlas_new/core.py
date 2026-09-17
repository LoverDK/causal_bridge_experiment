"""Mathematical primitives. No old-repository imports; target truth is never input."""
from itertools import product
import numpy as np
from scipy.optimize import linprog, minimize


def simplex(alpha):
    a = np.asarray(alpha, dtype=float)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError('Weights must be a finite vector')
    if a.min() < -1e-10 or abs(a.sum()-1) > 1e-7:
        raise ValueError('Weights must lie on the simplex')
    return a


def box_vertices(boxes):
    boxes = np.asarray(boxes, float)
    if boxes.ndim != 2 or boxes.shape[1] != 2 or not np.isfinite(boxes).all():
        raise ValueError('Expected finite one-dimensional intervals')
    if np.any(boxes[:, 0] > boxes[:, 1]):
        raise ValueError('Empty mechanism set')
    if len(boxes) > 15:
        raise ValueError('Exact enumeration capped at 15 boxes')
    return np.array(list(product(*boxes)))


def geometry(alpha, vertices, L, H):
    """Exact joint supremum for 1D boxes: G is convex in the mechanism tuple.

    For alpha>=0, diag(alpha)-alpha alpha^T is PSD. Adding absolute
    target-to-barycenter error preserves convexity; a box maximum is at vertices.
    The objective need NOT be convex as a function of alpha.
    """
    a = simplex(alpha)
    mean = vertices[:, :-1] @ a
    dispersion = (vertices[:, :-1]**2) @ a - mean**2
    return float(np.max(L*np.abs(vertices[:, -1]-mean) + H/2*np.maximum(dispersion, 0)))


def radius(alpha, vertices, L, H, noise_sd, beta, zeta=.05, mode='simultaneous'):
    a = simplex(alpha)
    if L < 0 or H < 0 or not 0 < zeta < 1:
        raise ValueError('Invalid scientific constants or failure budget')
    s, b = np.asarray(noise_sd), np.asarray(beta)
    if len(s) != len(a) or len(b) != len(a) or np.any(s < 0) or np.any(b < 0):
        raise ValueError('Invalid noise/bias envelope')
    bias = geometry(a, vertices, L, H) + float(a @ b)
    if mode == 'simultaneous':
        noise = np.sqrt(2*np.log(2*len(a)/zeta))*float(a@s)
    elif mode == 'fixed':
        noise = np.sqrt(2*np.log(2/zeta))*np.linalg.norm(a*s)
    else:
        raise ValueError(mode)
    return bias + float(noise)


def optimize_radius(boxes, L, H, noise_sd, beta, zeta=.05):
    """Multi-start feasible optimization, NOT certified global minimization.

    The data interface contains design and audited sets only, not observed effects.
    On solver failure a valid uniform-weight certificate remains available.
    """
    vertices = box_vertices(boxes)
    k = len(boxes)-1
    uniform = np.full(k, 1/k)
    def f(a):
        # SLSQP can evaluate infeasible intermediate iterates. Extend the objective
        # by normalization; the PUBLIC radius API still requires simplex inputs.
        a = np.maximum(np.asarray(a, float), 0.)
        a = a/a.sum() if a.sum() > 0 else uniform
        return radius(a, vertices, L, H, noise_sd, beta, zeta)
    candidates = [(f(uniform), uniform)]
    successes, failures = 0, 0
    centers = np.asarray(boxes).mean(axis=1)
    near = int(np.argmin(abs(centers[:-1]-centers[-1])))
    starts = [uniform, np.eye(k)[near], np.eye(k)[np.argmin(noise_sd)]]
    for start in starts:
        result = minimize(f, start, method='SLSQP', bounds=[(0, 1)]*k,
                          constraints={'type': 'eq', 'fun': lambda a: a.sum()-1},
                          options={'maxiter': 120, 'ftol': 1e-8})
        if result.success and np.isfinite(result.x).all():
            a = np.maximum(result.x, 0); a /= a.sum()
            candidates.append((f(a), a)); successes += 1
        else:
            failures += 1
    value, alpha = min(candidates, key=lambda x: x[0])
    return alpha, value, {'solver_successes': successes, 'solver_failures': failures,
                          'global_optimum_certified': False,
                          'fallback': successes == 0}


def calibrated_quantile(scores, eta):
    scores = np.asarray(scores)
    if scores.ndim != 1 or not 0 < eta < 1:
        raise ValueError('Invalid calibration input')
    rank = int(np.ceil((len(scores)+1)*(1-eta)))
    return float(np.sort(scores)[rank-1]) if rank <= len(scores) else float('inf')


def sharp_lipschitz(x, target, lower, upper, L):
    """Sharp finite-metric LP; an infeasible region has no numerical width."""
    x = np.atleast_1d(np.asarray(x, float))
    lo, hi = np.asarray(lower, float), np.asarray(upper, float)
    if L < 0 or np.any(lo > hi) or len(lo) != len(x) or len(hi) != len(x):
        raise ValueError('Invalid LP constraints')
    if not len(x):
        return {'status': 'unbounded', 'lower': -np.inf, 'upper': np.inf, 'width': np.inf}
    nodes = np.r_[x, target]; n = len(nodes)
    rows, rhs = [], []
    for i in range(n):
        for j in range(i):
            row = np.zeros(n); row[i], row[j] = 1, -1
            rows.extend([row, -row]); rhs.extend([L*abs(nodes[i]-nodes[j])]*2)
    A, b = np.asarray(rows), np.asarray(rhs)
    bounds = list(zip(lo, hi)) + [(None, None)]
    c = np.zeros(n); c[-1] = 1
    low = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    high = linprog(-c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    if low.status == 2 or high.status == 2:
        return {'status': 'infeasible', 'lower': np.nan, 'upper': np.nan, 'width': np.nan}
    if not low.success or not high.success:
        raise RuntimeError(f'LP numerical failure: {low.message}; {high.message}')
    violation = max(float(np.max(A@low.x-b)), float(np.max(A@high.x-b)), 0.)
    return {'status': 'optimal', 'lower': low.fun, 'upper': -high.fun,
            'width': max(0., -high.fun-low.fun), 'lower_witness': low.x.tolist(),
            'upper_witness': high.x.tolist(), 'max_pairwise_violation': violation}


def posterior(prior, design, sigma, selected):
    precision = np.linalg.inv(prior)
    for b in selected:
        precision += np.outer(design[b], design[b])/sigma[b]**2
    return np.linalg.inv(precision)


def information(prior, covariance):
    s1, v1 = np.linalg.slogdet(prior); s2, v2 = np.linalg.slogdet(covariance)
    if min(s1, s2) <= 0: raise ValueError('Covariance must be positive definite')
    return float((v1-v2)/2)


def logdet_greedy(prior, design, sigma, budget):
    selected = []
    for _ in range(budget):
        v = posterior(prior, design, sigma, selected)
        gains = [.5*np.log1p(x@v@x/s**2) if i not in selected else -np.inf
                 for i, (x, s) in enumerate(zip(design, sigma))]
        selected.append(int(np.argmax(gains)))
    return tuple(selected)


def complementarity():
    equations = np.array([[1., 1.], [0., 1.]])
    result = []
    for selected in [(), (0,), (1,), (0, 1)]:
        A = equations[list(selected)] if selected else None
        b = np.zeros(len(selected)) if selected else None
        low = linprog([1, 0], A_eq=A, b_eq=b, bounds=[(-1, 1)]*2, method='highs')
        high = linprog([-1, 0], A_eq=A, b_eq=b, bounds=[(-1, 1)]*2, method='highs')
        if not low.success or not high.success: raise RuntimeError('Witness LP failed')
        result.append({'selected': str(selected), 'width': -high.fun-low.fun})
    return result
