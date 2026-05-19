import math
from dataclasses import dataclass, field
from typing import List, Optional

EPS = 1e-9


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def distance(self, other: "Point") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Segment:
    name: str
    p1: Point
    p2: Point
    edge: Optional[object] = field(default=None, hash=False, compare=False)


def almost_equal(a: float, b: float) -> bool:
    return abs(a - b) < EPS


def orient2d(a: Point, b: Point, c: Point) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def point_on_segment(p: Point, a: Point, b: Point) -> bool:
    if abs(orient2d(a, b, p)) > EPS:
        return False

    return (
        min(a.x, b.x) - EPS <= p.x <= max(a.x, b.x) + EPS
        and
        min(a.y, b.y) - EPS <= p.y <= max(a.y, b.y) + EPS
    )


def line_intersection(a1, a2, b1, b2):
    x1, y1 = a1.x, a1.y
    x2, y2 = a2.x, a2.y
    x3, y3 = b1.x, b1.y
    x4, y4 = b2.x, b2.y

    den = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)

    if abs(den) < EPS:
        return None

    px = (
        (x1*y2 - y1*x2)*(x3 - x4)
        -
        (x1 - x2)*(x3*y4 - y3*x4)
    ) / den

    py = (
        (x1*y2 - y1*x2)*(y3 - y4)
        -
        (y1 - y2)*(x3*y4 - y3*x4)
    ) / den

    return Point(px, py)
def segment_intersection(s1: Segment, s2: Segment):
    p = line_intersection(s1.p1, s1.p2, s2.p1, s2.p2)

    if p is None:
        return None

    if (
        point_on_segment(p, s1.p1, s1.p2)
        and
        point_on_segment(p, s2.p1, s2.p2)
    ):
        return p

    return None


def shoelace(points: List[Point]) -> float:
    area = 0.0

    n = len(points)

    for i in range(n):
        j = (i + 1) % n

        area += (
            points[i].x * points[j].y
            -
            points[j].x * points[i].y
        )

    return area / 2.0


def angle(origin: Point, target: Point) -> float:
    return math.atan2(target.y - origin.y, target.x - origin.x)


def point_in_polygon(p: Point, polygon: List[Point]) -> bool:
    inside = False

    n = len(polygon)

    for i in range(n):
        j = (i + 1) % n

        xi, yi = polygon[i].x, polygon[i].y
        xj, yj = polygon[j].x, polygon[j].y

        intersect = (
            ((yi > p.y) != (yj > p.y))
            and
            (
                p.x
                <
                (xj - xi) * (p.y - yi) / (yj - yi + EPS) + xi
            )
        )

        if intersect:
            inside = not inside

    return inside