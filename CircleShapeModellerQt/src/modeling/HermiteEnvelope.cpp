#include "HermiteEnvelope.h"
#include <cmath>

namespace modeling {
using namespace geom;
static Vec2 hermite(const Vec2& p0, const Vec2& m0, const Vec2& p1, const Vec2& m1, double t) {
    const double t2=t*t, t3=t2*t;
    return p0*(2*t3-3*t2+1) + m0*(t3-2*t2+t) + p1*(-2*t3+3*t2) + m1*(t3-t2);
}
Shape HermiteEnvelope::generate(const std::vector<Circle>& circles, int resolution) const {
    Shape out;
    if (circles.size() < 2) { out.error = "Place at least two circles to generate an envelope."; return out; }
    for (const auto& c : circles) if (!finite(c.center) || !std::isfinite(c.radius) || c.radius <= kEpsilon) { out.error="Every circle must have a finite centre and a positive radius."; return out; }
    resolution = std::max(8, resolution);
    std::vector<Vec2> plusA, plusB, minusA, minusB;
    for (std::size_t i=0; i+1<circles.size(); ++i) {
        const auto& a=circles[i]; const auto& b=circles[i+1];
        const Vec2 delta=b.center-a.center; const double d=delta.length();
        if (d <= kEpsilon) { out.warnings.push_back("Consecutive circles have identical centres; this pair was skipped."); continue; }
        if (d <= std::abs(a.radius-b.radius)+kEpsilon) {
            out.warnings.push_back("No two real common external tangents exist for circles " + std::to_string(a.id) + " and " + std::to_string(b.id) + ". Pair skipped.");
            continue;
        }
        const Vec2 u=delta/d, n=u.perpendicular();
        const double alpha=clamp((a.radius-b.radius)/d,-1.0,1.0);
        const double q=std::sqrt(std::max(0.0,1.0-alpha*alpha));
        const Vec2 normal1=u*alpha+n*q, normal2=u*alpha-n*q;
        const Vec2 p0=a.center+normal1*a.radius, p1=b.center+normal1*b.radius;
        const Vec2 m0=u*d, m1=u*d;
        const Vec2 q0=a.center+normal2*a.radius, q1=b.center+normal2*b.radius;
        for(int k=0;k<=resolution;++k) {
            const double t=static_cast<double>(k)/resolution;
            plusA.push_back(hermite(p0,m0,p1,m1,t));
            minusA.push_back(hermite(q0,m0,q1,m1,t));
        }
        out.contactPoints.insert(out.contactPoints.end(),{p0,p1,q0,q1});
        out.tangentVectors.push_back({p0,m0}); out.tangentVectors.push_back({q0,m0});
    }
    if (plusA.empty()) { out.error="No valid circle pairs were available for envelope generation."; return out; }
    // Keep each segment in creation order. Remove duplicate join samples.
    auto append = [](std::vector<Vec2>& dst, const std::vector<Vec2>& src) {
        std::size_t start = (!dst.empty() && !src.empty() && (dst.back()-src.front()).length()<1e-6) ? 1 : 0;
        dst.insert(dst.end(),src.begin()+static_cast<std::ptrdiff_t>(start),src.end());
    };
    append(out.upper,plusA); append(out.lower,minusA);
    out.valid = out.upper.size()>=2 && out.lower.size()>=2;
    if (!out.valid) out.error="The envelope could not be generated from the supplied circles.";
    if (circles.size()>2) out.warnings.push_back("Piecewise Hermite segments use local external tangents. At sharp changes in direction, inspect joins for curvature discontinuities.");
    return out;
}
}
