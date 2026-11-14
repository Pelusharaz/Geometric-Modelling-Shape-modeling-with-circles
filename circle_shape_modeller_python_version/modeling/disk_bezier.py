"""Disk-Bézier centreline with normal-offset thickness approximation."""
from geometry.primitives import Point, Shape
from geometry.curves import bezier, bezier_derivative
from .base import ShapeModelingMethod

class DiskBezier(ShapeModelingMethod):
    name = 'Disk-Bézier'
    def generate(self, circles, resolution=120):
        if len(circles) < 2: raise ValueError('Place at least two circles to generate a Disk-Bézier shape.')
        if any(c.radius <= 0 for c in circles): raise ValueError('All circle radii must be positive.')
        centers=[c.center for c in circles]; radii=[c.radius for c in circles]
        upper=[]; lower=[]; centerline=[]; warnings=[]
        for k in range(resolution+1):
            t=k/resolution
            p=bezier(centers,t); r=bezier([Point(v,0) for v in radii],t).x
            derivative=bezier_derivative(centers,t)
            if derivative.length()<1e-8:
                # A symmetric finite difference is a stable fallback near stationary points.
                ta=max(0,t-1e-4); tb=min(1,t+1e-4)
                derivative=bezier(centers,tb)-bezier(centers,ta)
            if derivative.length()<1e-8:
                warnings.append('The centreline derivative is zero; boundary samples near this parameter were omitted.')
                continue
            normal=derivative.normalized().perpendicular()
            centerline.append(p); upper.append(p+normal*r); lower.append(p-normal*r)
        # Curvature-radius warning: offset curves can cusp when |kappa| * r >= 1.
        for i in range(1,len(centerline)-1):
            v1=centerline[i]-centerline[i-1]; v2=centerline[i+1]-centerline[i]
            if v1.length()>1e-8 and v2.length()>1e-8:
                turn=abs(v1.x*v2.y-v1.y*v2.x)/(v1.length()*v2.length())
                local_r=(radii[0]+radii[-1])/2
                if turn*local_r/max((v1.length()+v2.length())/2,1e-8)>0.8:
                    warnings.append('High curvature relative to thickness detected. Normal offsets may form cusps or self-intersections.')
                    break
        return Shape(upper,lower,centerline,warnings,[],[],self.name)
