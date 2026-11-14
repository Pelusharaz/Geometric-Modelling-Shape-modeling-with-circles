#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <string>
#include <vector>

namespace geom {
constexpr double kEpsilon = 1e-9;
struct Vec2 {
    double x{0.0}, y{0.0};
    Vec2 operator+(const Vec2& o) const { return {x + o.x, y + o.y}; }
    Vec2 operator-(const Vec2& o) const { return {x - o.x, y - o.y}; }
    Vec2 operator*(double s) const { return {x * s, y * s}; }
    Vec2 operator/(double s) const { return {x / s, y / s}; }
    double dot(const Vec2& o) const { return x * o.x + y * o.y; }
    double cross(const Vec2& o) const { return x * o.y - y * o.x; }
    double lengthSquared() const { return dot(*this); }
    double length() const { return std::sqrt(lengthSquared()); }
    Vec2 normalized() const { const double n = length(); return n > kEpsilon ? *this / n : Vec2{}; }
    Vec2 perpendicular() const { return {-y, x}; }
};
inline Vec2 operator*(double s, const Vec2& v) { return v * s; }
struct Circle { int id{0}; Vec2 center; double radius{20.0}; };
struct Shape {
    std::vector<Vec2> upper, lower, centerline;
    std::vector<Vec2> contactPoints;
    std::vector<std::pair<Vec2, Vec2>> tangentVectors;
    std::vector<std::string> warnings;
    bool valid{false};
    std::string error;
};
inline bool finite(const Vec2& p) { return std::isfinite(p.x) && std::isfinite(p.y); }
inline double clamp(double v, double lo, double hi) { return std::max(lo, std::min(hi, v)); }
}
