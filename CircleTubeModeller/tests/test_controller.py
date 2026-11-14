import pytest
from circletube.interaction.circle_controller import CircleController


def test_order_ids_undo_redo_and_persistence():
    c = CircleController()
    a, b, d = c.add_circle(0, 0, 10), c.add_circle(50, 0, 10), c.add_circle(100, 0, 10)
    assert [x.order for x in c.circles] == [0, 1, 2] and len({a.id, b.id, d.id}) == 3
    c.remove(b.id)
    assert [x.id for x in c.circles] == [a.id, d.id] and [x.order for x in c.circles] == [0, 1]
    e = c.add_circle(5, 5, 5)
    assert e.id not in (a.id, b.id, d.id)                 # ids never reused
    c.undo(); c.undo()
    assert [x.id for x in c.circles] == [a.id, b.id, d.id]
    c.redo()
    assert len(c) == 2
    c.update(a.id, x=3, y=4, r=7)
    assert (c.get(a.id).x, c.get(a.id).y, c.get(a.id).radius) == (3, 4, 7)
    c.undo()
    assert c.get(a.id).radius == 10
    txt = c.to_json(); c2 = CircleController(); c2.load_json(txt)
    assert [(x.id, x.x, x.radius) for x in c2.circles] == [(x.id, x.x, x.radius) for x in c.circles]


def test_invalid_input_rejected():
    c = CircleController()
    for args in ((0, 0, 0), (0, 0, -1), (float("nan"), 0, 5), (0, 0, float("inf"))):
        with pytest.raises(ValueError):
            c.add_circle(*args)
    assert len(c) == 0


def test_clear_and_selection():
    c = CircleController(); a = c.add_circle(0, 0, 5)
    assert c.selected_id == a.id
    c.clear(); assert len(c) == 0 and c.selected is None
    c.undo(); assert len(c) == 1
