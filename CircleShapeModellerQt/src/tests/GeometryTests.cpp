#include "modeling/HermiteEnvelope.h"
#include "modeling/DiskBezier.h"
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
    using namespace geom;
    std::vector<Circle> pair{{1,{0,0},30},{2,{150,0},30}};
    modeling::HermiteEnvelope h;auto hs=h.generate(pair,40);assert(hs.valid);assert(!hs.upper.empty()&&!hs.lower.empty());
    auto unequal=pair;unequal[1].radius=45;assert(h.generate(unequal,40).valid);
    modeling::DiskBezier b;auto bs=b.generate({{1,{0,0},20},{2,{100,50},30},{3,{200,0},25}},80);assert(bs.valid);assert(bs.centerline.size()==81);assert(std::abs(bs.centerline.front().x)<1e-8);assert(std::abs(bs.centerline.back().x-200)<1e-8);
    auto invalid=pair;invalid[0].radius=-1;assert(!b.generate(invalid,40).valid);
    auto contained=std::vector<Circle>{{1,{0,0},100},{2,{10,0},10}};auto result=h.generate(contained,40);assert(!result.valid);
    std::cout<<"All geometry tests passed.\n";
}
