#pragma once
#include "geometry/Geometry.h"
#include <string>
namespace modeling {
class ShapeModelingMethod {
public:
    virtual ~ShapeModelingMethod() = default;
    virtual std::string name() const = 0;
    virtual geom::Shape generate(const std::vector<geom::Circle>& circles, int resolution) const = 0;
};
}
