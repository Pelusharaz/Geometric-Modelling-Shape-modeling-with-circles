import unittest
from geometry.primitives import Circle, Point
from modeling.hermite_envelope import HermiteEnvelope
from modeling.disk_bezier import DiskBezier

class GeometryTests(unittest.TestCase):
    def setUp(self): self.chain=[Circle(1,Point(0,0),30),Circle(2,Point(100,0),30),Circle(3,Point(180,55),22)]
    def test_hermite_generates_two_boundaries(self):
        s=HermiteEnvelope().generate(self.chain,40)
        self.assertGreater(len(s.upper),40); self.assertEqual(len(s.upper),len(s.lower))
    def test_equal_radius_tangent_contacts(self):
        s=HermiteEnvelope().generate(self.chain[:2],30)
        self.assertAlmostEqual(s.contact_points[0].y,30,places=6)
        self.assertAlmostEqual(s.contact_points[1].y,30,places=6)
    def test_contained_pair_is_reported(self):
        cs=[Circle(1,Point(0,0),80),Circle(2,Point(10,0),10)]
        with self.assertRaises(ValueError): HermiteEnvelope().generate(cs)
    def test_disk_bezier_interpolates_endpoints(self):
        s=DiskBezier().generate(self.chain,60)
        self.assertAlmostEqual(s.centerline[0].x,0,places=6)
        self.assertAlmostEqual(s.centerline[-1].x,180,places=6)
        self.assertEqual(len(s.upper),len(s.lower))
    def test_invalid_radius_rejected(self):
        with self.assertRaises(ValueError): DiskBezier().generate([Circle(1,Point(0,0),-2),Circle(2,Point(3,0),2)])

if __name__=='__main__': unittest.main()
