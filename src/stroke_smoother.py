"""
Advanced Stroke Smoothing Module
─────────────────────────────────
Provides multiple smoothing algorithms to produce fluid,
natural-looking handwriting strokes for ALL character types
(letters, numbers, special symbols).

Pipeline order:
  1. remove_duplicates()      — clean coincident points
  2. remove_outliers()        — remove spike noise from raw strokes
  3. resample_stroke()        — uniform arc-length spacing
  4. chaikin_smooth()         — geometric corner cutting
  5. cubic_spline_smooth()    — C² continuous curves
  6. gaussian_smooth()        — final soft pass
  7. douglas_peucker()        — optional point reduction
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline


# ────────────────────────────────────────────────────────────────
# 0a. DUPLICATE REMOVAL
# ────────────────────────────────────────────────────────────────

def remove_duplicates(stroke, min_dist=0.01):
    """Remove consecutive points that are essentially the same."""
    if len(stroke) < 2:
        return stroke
    pts = np.array(stroke, dtype=float)
    keep = [0]
    for i in range(1, len(pts)):
        if np.hypot(pts[i, 0] - pts[keep[-1], 0],
                    pts[i, 1] - pts[keep[-1], 1]) > min_dist:
            keep.append(i)
    if keep[-1] != len(pts) - 1:
        keep.append(len(pts) - 1)
    return pts[keep].tolist()


# ────────────────────────────────────────────────────────────────
# 0b. OUTLIER / SPIKE REMOVAL
# ────────────────────────────────────────────────────────────────

def remove_outliers(stroke, threshold=3.0):
    """
    Remove points that deviate too far from their neighbours
    (spikes from noisy skeleton extraction).  A point is an outlier
    if its distance to the midpoint of its neighbours exceeds
    threshold × median segment length.
    """
    if len(stroke) < 5:
        return stroke
    pts = np.array(stroke, dtype=float)
    diffs = np.diff(pts, axis=0)
    seg_lens = np.hypot(diffs[:, 0], diffs[:, 1])
    median_seg = np.median(seg_lens)
    if median_seg < 1e-6:
        return stroke

    keep = [0]
    for i in range(1, len(pts) - 1):
        mid = (pts[i - 1] + pts[i + 1]) / 2.0
        dev = np.hypot(pts[i, 0] - mid[0], pts[i, 1] - mid[1])
        if dev < threshold * median_seg:
            keep.append(i)
    keep.append(len(pts) - 1)
    return pts[keep].tolist()


# ────────────────────────────────────────────────────────────────
# 1. RESAMPLING — uniform arc-length spacing
# ────────────────────────────────────────────────────────────────

def resample_stroke(stroke, num_points=None, spacing_mm=0.3):
    """
    Resample a stroke so points are evenly spaced along the arc.

    Parameters
    ----------
    stroke : list of [x, y]
    num_points : int or None
        Fixed number of output points.  If None, the spacing_mm
        parameter is used to decide the count.
    spacing_mm : float
        Desired distance between consecutive points (mm).
        Ignored when num_points is set.

    Returns
    -------
    list of [x, y]
    """
    pts = np.array(stroke, dtype=float)
    if len(pts) < 2:
        return stroke

    # cumulative arc length
    diffs = np.diff(pts, axis=0)
    seg_lens = np.hypot(diffs[:, 0], diffs[:, 1])
    cum = np.concatenate(([0.0], np.cumsum(seg_lens)))
    total_len = cum[-1]

    if total_len < 1e-6:
        return stroke

    if num_points is None:
        num_points = max(4, int(total_len / spacing_mm))

    # interpolate at uniform arc-length positions
    targets = np.linspace(0.0, total_len, num_points)
    new_x = np.interp(targets, cum, pts[:, 0])
    new_y = np.interp(targets, cum, pts[:, 1])
    return np.column_stack((new_x, new_y)).tolist()


# ────────────────────────────────────────────────────────────────
# 2. CHAIKIN'S CORNER-CUTTING
# ────────────────────────────────────────────────────────────────

def chaikin_smooth(stroke, iterations=2):
    """
    Chaikin's corner-cutting algorithm.  Each iteration replaces
    every segment with two new points at 25 % and 75 % along the
    segment, gradually rounding sharp corners while preserving the
    overall shape.

    Parameters
    ----------
    stroke : list of [x, y]
    iterations : int   (1-3 is typical)
    """
    pts = np.array(stroke, dtype=float)
    if len(pts) < 3:
        return stroke

    for _ in range(iterations):
        new_pts = [pts[0]]          # keep first endpoint
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            q = 0.75 * p0 + 0.25 * p1
            r = 0.25 * p0 + 0.75 * p1
            new_pts.append(q)
            new_pts.append(r)
        new_pts.append(pts[-1])     # keep last endpoint
        pts = np.array(new_pts)

    return pts.tolist()


# ────────────────────────────────────────────────────────────────
# 3. CUBIC SPLINE INTERPOLATION  (C² smooth)
# ────────────────────────────────────────────────────────────────

def cubic_spline_smooth(stroke, num_points=None, factor=2.0):
    """
    Fit a natural cubic spline through the stroke points and
    re-evaluate at a higher density.  This guarantees C² (second-
    derivative) continuity — the smoothest possible curve that
    passes through the original points.

    Parameters
    ----------
    stroke : list of [x, y]
    num_points : int or None
        Output point count.  Default = len(stroke) * factor.
    factor : float
        Multiplier for output density when num_points is None.
    """
    pts = np.array(stroke, dtype=float)
    if len(pts) < 4:
        return stroke

    # parameterise by cumulative chord length
    diffs = np.diff(pts, axis=0)
    chord = np.hypot(diffs[:, 0], diffs[:, 1])
    t = np.concatenate(([0.0], np.cumsum(chord)))
    total = t[-1]

    if total < 1e-6:
        return stroke

    cs_x = CubicSpline(t, pts[:, 0], bc_type='natural')
    cs_y = CubicSpline(t, pts[:, 1], bc_type='natural')

    if num_points is None:
        num_points = max(len(pts), int(len(pts) * factor))

    t_new = np.linspace(0.0, total, num_points)
    new_x = cs_x(t_new)
    new_y = cs_y(t_new)
    return np.column_stack((new_x, new_y)).tolist()


# ────────────────────────────────────────────────────────────────
# 4. GAUSSIAN LOW-PASS
# ────────────────────────────────────────────────────────────────

def gaussian_smooth(stroke, sigma=1.4):
    """
    Apply a 1-D Gaussian filter independently to X and Y.
    Endpoints are preserved exactly to avoid shrinkage.

    Parameters
    ----------
    stroke : list of [x, y]
    sigma : float  (higher → smoother,  1.0-2.0 recommended)
    """
    pts = np.array(stroke, dtype=float)
    if len(pts) < 4:
        return stroke

    # save endpoints
    start, end = pts[0].copy(), pts[-1].copy()

    sx = gaussian_filter1d(pts[:, 0], sigma, mode='nearest')
    sy = gaussian_filter1d(pts[:, 1], sigma, mode='nearest')

    # pin endpoints back
    sx[0], sy[0] = start
    sx[-1], sy[-1] = end

    return np.column_stack((sx, sy)).tolist()


# ────────────────────────────────────────────────────────────────
# 5. FULL SMOOTHING PIPELINE  (one-call convenience)
# ────────────────────────────────────────────────────────────────

def smooth_stroke(stroke,
                  resample_spacing=0.25,
                  chaikin_iters=3,
                  spline_factor=2.5,
                  gauss_sigma=2.0):
    """
    Run the complete smoothing pipeline on a single stroke.
    Works on ALL character types: letters, numbers, symbols.

    Parameters
    ----------
    stroke : list of [x, y]
    resample_spacing  : point spacing for resampling (mm)
    chaikin_iters     : corner-cutting passes (3 = very smooth)
    spline_factor     : cubic-spline density multiplier
    gauss_sigma       : final Gaussian sigma (2.0 = generous)

    Returns
    -------
    list of [x, y]  — smoothed stroke
    """
    if len(stroke) < 3:
        return stroke

    # Stage 0: Clean raw data (removes noise from skeleton extraction)
    s = remove_duplicates(stroke, min_dist=0.005)
    s = remove_outliers(s, threshold=2.5)

    if len(s) < 3:
        return stroke

    # Stage 1: Uniform arc-length resampling
    s = resample_stroke(s, spacing_mm=resample_spacing)

    # Stage 2: Chaikin corner-cutting (rounds sharp angles)
    s = chaikin_smooth(s, iterations=chaikin_iters)

    # Stage 3: Cubic spline (C² continuity — perfectly smooth curves)
    s = cubic_spline_smooth(s, factor=spline_factor)

    # Stage 4: Gaussian low-pass (removes any remaining micro-roughness)
    s = gaussian_smooth(s, sigma=gauss_sigma)

    # Stage 5: Final resample to keep point count reasonable for G-code
    s = resample_stroke(s, spacing_mm=0.4)

    return s
