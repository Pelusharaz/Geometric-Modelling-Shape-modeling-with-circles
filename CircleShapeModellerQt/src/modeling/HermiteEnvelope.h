#pragma once
#include "ShapeModelingMethod.h"
namespace modeling {
class HermiteEnvelope final : public ShapeModelingMethod {
public:
    std::string name() const override { return "Hermite Circle Envelope"; }
    geom::Shape generate(const std::vector<geom::Circle>& circles, int resolution) const override;
};
}
