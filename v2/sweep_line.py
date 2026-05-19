import heapq

from geometry import (
    Segment,
    segment_intersection,
    EPS
)

from structures.avl import AVLTree


class Event:

    def __init__(self, point):
        self.point = point

        self.upper = set()
        self.lower = set()
        self.cross = set()


class SweepLine:

    def __init__(self):

        self.y = 0.0

        self.events = []

        self.event_map = {}

        self.intersections = []

        self.status = AVLTree(self.key)

    def x_at_y(self, segment, y):

        p1 = segment.p1
        p2 = segment.p2

        if abs(p1.y - p2.y) < EPS:
            return min(p1.x, p2.x)

        t = (y - p1.y) / (p2.y - p1.y)

        return p1.x + t * (p2.x - p1.x)

    def key(self, segment):

        return (
            self.x_at_y(segment, self.y),
            segment.name
        )

    def add_segment(self, segment):

        upper = segment.p1
        lower = segment.p2

        if (
            lower.y > upper.y
            or
            (
                abs(lower.y - upper.y) < EPS
                and
                lower.x < upper.x
            )
        ):
            upper, lower = lower, upper

        if upper not in self.event_map:
            self.event_map[upper] = Event(upper)

        if lower not in self.event_map:
            self.event_map[lower] = Event(lower)

        self.event_map[upper].upper.add(segment)
        self.event_map[lower].lower.add(segment)

    def initialize_queue(self):

        for event in self.event_map.values():

            heapq.heappush(
                self.events,
                (
                    -event.point.y,
                    event.point.x,
                    event
                )
            )

    def find_intersections_naive(self):
        """
        Temporal.
        Luego puede sustituirse
        por Bentley-Ottmann completo.
        """

        segments = []

        for event in self.event_map.values():

            for s in event.upper:
                segments.append(s)

        n = len(segments)

        for i in range(n):

            for j in range(i + 1, n):

                s1 = segments[i]
                s2 = segments[j]

                p = segment_intersection(s1, s2)

                if p is not None:

                    self.intersections.append(
                        (
                            p,
                            [s1, s2]
                        )
                    )

    def run(self):

        self.initialize_queue()

        self.find_intersections_naive()

        return self.intersections