#include "ModelingFactory.h"
#include "HermiteEnvelope.h"
#include "DiskBezier.h"
namespace modeling {
std::vector<std::string> ModelingFactory::names(){return {"Hermite Circle Envelope","Disk-Bézier"};}
std::unique_ptr<ShapeModelingMethod> ModelingFactory::create(const std::string& name){
    if(name=="Hermite Circle Envelope") return std::make_unique<HermiteEnvelope>();
    if(name=="Disk-Bézier") return std::make_unique<DiskBezier>();
    return nullptr;
}
}
