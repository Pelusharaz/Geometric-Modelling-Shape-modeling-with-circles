#include "DiskBezier.h"
#include <cmath>
#include <limits>
namespace modeling {
using namespace geom;
static double choose(int n,int k) { double v=1.0; for(int i=1;i<=k;++i) v=v*(n-k+i)/i; return v; }
static Vec2 evaluate(const std::vector<Circle>& c,double t) {
    const int n=static_cast<int>(c.size())-1; Vec2 p{};
    for(int i=0;i<=n;++i) p=p+(c[static_cast<std::size_t>(i)].center*(choose(n,i)*std::pow(1-t,n-i)*std::pow(t,i)));
    return p;
}
static double evaluateRadius(const std::vector<Circle>& c,double t) {
    const int n=static_cast<int>(c.size())-1; double r=0;
    for(int i=0;i<=n;++i) r+=c[static_cast<std::size_t>(i)].radius*choose(n,i)*std::pow(1-t,n-i)*std::pow(t,i);
    return r;
}
Shape DiskBezier::generate(const std::vector<Circle>& circles,int resolution) const {
    Shape out;
    if(circles.size()<2){out.error="Place at least two control circles to generate a Disk-Bézier shape.";return out;}
    for(const auto& c:circles) if(!finite(c.center)||!std::isfinite(c.radius)||c.radius<=kEpsilon){out.error="Every control circle must have a finite centre and a positive radius.";return out;}
    resolution=std::max(24,resolution);
    const double dt=1.0/static_cast<double>(resolution);
    for(int i=0;i<=resolution;++i){
        const double t=static_cast<double>(i)/resolution;
        const Vec2 p=evaluate(circles,t);
        // Analytic derivative of a degree-n Bezier: n times the Bezier of first differences.
        const int n=static_cast<int>(circles.size())-1; Vec2 derivative{};
        for(int j=0;j<n;++j){
            const double w=choose(n-1,j)*std::pow(1-t,n-1-j)*std::pow(t,j);
            derivative=derivative+(circles[static_cast<std::size_t>(j+1)].center-circles[static_cast<std::size_t>(j)].center)*(n*w);
        }
        if(derivative.length()<=kEpsilon){
            const double ta=std::max(0.0,t-dt), tb=std::min(1.0,t+dt);
            derivative=evaluate(circles,tb)-evaluate(circles,ta);
        }
        if(derivative.length()<=kEpsilon){out.warnings.push_back("A near-zero centreline derivative was encountered; a local fallback direction was used."); derivative={1,0};}
        const Vec2 normal=derivative.normalized().perpendicular();
        const double r=evaluateRadius(circles,t);
        out.centerline.push_back(p); out.upper.push_back(p+normal*r); out.lower.push_back(p-normal*r);
    }
    // Detect likely offset singularities: radius * curvature >= 1.
    for(std::size_t i=1;i+1<out.centerline.size();++i){
        const Vec2 a=out.centerline[i]-out.centerline[i-1], b=out.centerline[i+1]-out.centerline[i];
        const double la=a.length(),lb=b.length(); if(la<=kEpsilon||lb<=kEpsilon) continue;
        const double turn=std::atan2(a.cross(b),a.dot(b));
        const double curvature=std::abs(turn)/std::max(kEpsilon,0.5*(la+lb));
        if(evaluateRadius(circles,static_cast<double>(i)/resolution)*curvature>=0.95){out.warnings.push_back("Radius is large relative to local curvature. Normal-offset boundaries may form cusps or self-intersections.");break;}
    }
    out.valid=true; return out;
}
}
