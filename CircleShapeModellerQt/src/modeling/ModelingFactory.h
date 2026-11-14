#pragma once
#include "ShapeModelingMethod.h"
#include <memory>
#include <string>
#include <vector>
namespace modeling {
class ModelingFactory {
public:
    static std::vector<std::string> names();
    static std::unique_ptr<ShapeModelingMethod> create(const std::string& name);
};
}
