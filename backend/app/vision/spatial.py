from typing import List, Tuple

Point2D = Tuple[float, float]
Polygon2D = List[List[float]]

def is_point_in_polygon(point: Point2D, polygon: Polygon2D) -> bool:
    """
    Determines whether a 2D point (x, y) lies inside a polygon using the Ray-Casting Algorithm (Even-Odd Rule).
    
    :param point: Tuple (x, y) of the query point.
    :param polygon: List of [x, y] coordinates defining polygon vertices.
    :return: True if point is inside or on the boundary of the polygon, False otherwise.
    """
    x, y = point
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = polygon[0]

    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

def get_bbox_bottom_center(bbox: List[float]) -> Point2D:
    """
    Calculates the bottom-center point of a bounding box [x1, y1, x2, y2].
    This represents the ground contact / foot position of detected targets (people, vehicles).
    """
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2.0
    cy = float(y2)
    return (cx, cy)

def get_bbox_center(bbox: List[float]) -> Point2D:
    """Calculates the geometric center point of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return (cx, cy)

def is_bbox_in_polygon(bbox: List[float], polygon: Polygon2D, ref_point: str = "bottom_center") -> bool:
    """
    Checks if a target's bounding box intersects/enters a polygon based on reference point.
    
    :param bbox: [x1, y1, x2, y2]
    :param polygon: List of [x, y] vertex pairs
    :param ref_point: 'bottom_center' or 'center'
    :return: True if the reference point lies within the polygon
    """
    if ref_point == "bottom_center":
        pt = get_bbox_bottom_center(bbox)
    else:
        pt = get_bbox_center(bbox)

    return is_point_in_polygon(pt, polygon)

def _cross_product(a: Point2D, b: Point2D, c: Point2D) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def do_line_segments_intersect(p1: Point2D, p2: Point2D, q1: Point2D, q2: Point2D) -> bool:
    """
    Determines if line segment (p1 -> p2) intersects with line segment (q1 -> q2).
    Used for tripwire crossing detection.
    """
    cp1 = _cross_product(p1, p2, q1)
    cp2 = _cross_product(p1, p2, q2)
    cp3 = _cross_product(q1, q2, p1)
    cp4 = _cross_product(q1, q2, p2)

    if ((cp1 > 0 and cp2 < 0) or (cp1 < 0 and cp2 > 0)) and \
       ((cp3 > 0 and cp4 < 0) or (cp3 < 0 and cp4 > 0)):
        return True

    return False
