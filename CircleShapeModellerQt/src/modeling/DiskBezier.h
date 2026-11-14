#pragma once
#include "ShapeModelingMethod.h"
namespace modeling {
class DiskBezier final : public ShapeModelingMethod {
public:
    std::string name() const override { return "Disk-Bézier"; }
    geom::Shape generate(const std::vector<geom::Circle>& circles, int resolution) const override;
};
}
