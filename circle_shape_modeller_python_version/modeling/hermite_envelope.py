"""Piecewise common-tangent Hermite envelope for an ordered circle chain.

For each adjacent pair, the two common external tangent lines define the
upper/lower contact points. Hermite interpolation joins matching contacts.
This is a local, piecewise envelope construction, not the exact global
boundary of the union of all disks for arbitrary overlapping configurations.
"""
from math import sqrt
from geometry.primitives import Point, Shape
from geometry.curves import sample_hermite
from .base import ShapeModelingMethod

class HermiteEnvelope(ShapeModelingMethod):
    name = 'Hermite Circle Envelope'
    def generate(self, circles, resolution=80):
        if len(circles) < 2: raise ValueError('Place at least two circles to generate an envelope.')
        upper, lower, centerline, contacts, tangents, warnings = [], [], [], [], [], []
        for c in circles:
            if c.radius <= 0: raise ValueError(f'Circle {c.id} has a non-positive radius.')
        for a,b in zip(circles, circles[1:]):
            delta=b.center-a.center; d=delta.length()
            if d < 1e-8:
                warnings.append(f'Circles {a.id} and {b.id} have identical centres; this pair was skipped.')
                continue
            alpha=(a.radius-b.radius)/d
            if abs(alpha) > 1+1e-10:
                warnings.append(f'Circle {a.id} is contained by or too different in size from circle {b.id}; no real common external tangent exists.')
                continue
            alpha=max(-1.0,min(1.0,alpha)); q=sqrt(max(0.0,1-alpha*alpha))
            u=delta/d; n=u.perpendicular()
            n_top=u*alpha+n*q; n_bottom=u*alpha-n*q
            p0t=a.center+n_top*a.radius; p1t=b.center+n_top*b.radius
            p0b=a.center+n_bottom*a.radius; p1b=b.center+n_bottom*b.radius
            # The tangent direction is parallel to the centre-to-centre vector.
            # Scale handles are tied to chord length for stable local Hermite segments.
            handle=d*0.85
            top=sample_hermite(p0t,p1t,u*handle,u*handle,resolution)
            bot=sample_hermite(p0b,p1b,u*handle,u*handle,resolution)
            if upper: top=top[1:]; bot=bot[1:]
            upper.extend(top); lower.extend(bot)
            centerline.extend([a.center+(b.center-a.center)*(i/resolution) for i in range(resolution+1)][1:] if centerline else [a.center+(b.center-a.center)*(i/resolution) for i in range(resolution+1)])
            contacts.extend([p0t,p1t,p0b,p1b]); tangents.extend([(p0t,u*handle),(p1t,u*handle),(p0b,u*handle),(p1b,u*handle)])
            if d < a.radius+b.radius:
                warnings.append(f'Circles {a.id} and {b.id} overlap. The local tangent construction is valid, but the joined outline may not equal the exact union boundary.')
        if not upper: raise ValueError('No valid tangent segments could be generated. Adjust the circle positions or radii.')
        return Shape(upper,lower,centerline,warnings,contacts,tangents,self.name)
