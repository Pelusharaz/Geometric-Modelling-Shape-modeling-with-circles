"""Curve evaluation utilities."""
from math import comb
from .primitives import Point

def hermite(p0, p1, m0, m1, t):
    t2, t3 = t*t, t*t*t
    h00, h10 = 2*t3-3*t2+1, t3-2*t2+t
    h01, h11 = -2*t3+3*t2, t3-t2
    return p0*h00 + m0*h10 + p1*h01 + m1*h11

def bezier(points, t):
    n = len(points)-1
    result = Point(0, 0)
    for i, p in enumerate(points):
        result += p * (comb(n, i) * (1-t)**(n-i) * t**i)
    return result

def bezier_derivative(points, t):
    n = len(points)-1
    if n <= 0: return Point(0, 0)
    derivative_points = [(points[i+1]-points[i])*n for i in range(n)]
    return bezier(derivative_points, t)

def sample_hermite(p0, p1, m0, m1, resolution):
    return [hermite(p0,p1,m0,m1,i/resolution) for i in range(resolution+1)]
