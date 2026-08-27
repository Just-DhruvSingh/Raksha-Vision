from typing import List, Tuple, Union

Point2D = Tuple[float, float]
Polygon2D = Union[List[Tuple[float, float]], List[List[float]]]

def calculate_bottom_center(bbox: List[float]) -> Tuple[float, float]:
    """
    Calculates the bottom-center (x, y) point of a bounding box [x1, y1, x2, y2].
    This represents entity feet / ground contact position for spatial zone evaluation.
    """
    x1, y1, x2, y2 = bbox
    cx = (float(x1) + float(x2)) / 2.0
    cy = float(y2)
    return (cx, cy)

def get_bbox_bottom_center(bbox: List[float]) -> Tuple[float, float]:
    """Alias for calculate_bottom_center for backward compatibility."""
    return calculate_bottom_center(bbox)

def get_bbox_center(bbox: List[float]) -> Tuple[float, float]:
    """Calculates the geometric center point (x, y) of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    cx = (float(x1) + float(x2)) / 2.0
    cy = (float(y1) + float(y2)) / 2.0
    return (cx, cy)

def is_point_in_polygon(point: Tuple[float, float], polygon: Polygon2D) -> bool:
    """
    Determines whether a 2D point (x, y) lies inside or on the boundary of a polygon 
    using the Ray-Casting Algorithm (Even-Odd Rule).

    :param point: Tuple (x, y) representing point coordinates.
    :param polygon: List of (x, y) tuples or [x, y] lists defining polygon vertices.
    :return: True if point is inside or on boundary, False otherwise.
    """
    x, y = point
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = float(polygon[0][0]), float(polygon[0][1])

    for i in range(1, n + 1):
        p2x, p2y = float(polygon[i % n][0]), float(polygon[i % n][1])
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

def is_bbox_in_polygon(bbox: List[float], polygon: Polygon2D, ref_point: str = "bottom_center") -> bool:
    """
    Checks if a target's bounding box intersects/enters a polygon based on reference point.
    
    :param bbox: [x1, y1, x2, y2]
    :param polygon: Polygon vertex coordinates
    :param ref_point: 'bottom_center' or 'center'
    :return: True if reference point lies within polygon
    """
    if ref_point == "bottom_center":
        pt = calculate_bottom_center(bbox)
    else:
        pt = get_bbox_center(bbox)

    return is_point_in_polygon(pt, polygon)

def _cross_product(a: Point2D, b: Point2D, c: Point2D) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def do_line_segments_intersect(p1: Point2D, p2: Point2D, q1: Point2D, q2: Point2D) -> bool:
    """
    Determines if line segment (p1 -> p2) intersects with line segment (q1 -> q2).
    Used for tripwire line crossing detection.
    """
    cp1 = _cross_product(p1, p2, q1)
    cp2 = _cross_product(p1, p2, q2)
    cp3 = _cross_product(q1, q2, p1)
    cp4 = _cross_product(q1, q2, p2)

    if ((cp1 > 0 and cp2 < 0) or (cp1 < 0 and cp2 > 0)) and \
       ((cp3 > 0 and cp4 < 0) or (cp3 < 0 and cp4 > 0)):
        return True

    return False
