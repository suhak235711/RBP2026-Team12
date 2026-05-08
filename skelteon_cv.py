#!/usr/bin/env python3

import cv2
import numpy as np


def detect_monitor(image):
    """
    Detect four corner points of the monitor (the largest rectangle) in the image.
    """
    # NOTE: In this example, the four corner points of the monitor are provided.
    #       In the actual competition, you should detect the monitor corners by yourself.

    top_left = np.array([631, 862], dtype="float32")
    top_right = np.array([1526, 346], dtype="float32")
    bottom_right = np.array([2034, 636], dtype="float32")
    bottom_left = np.array([1139, 1152], dtype="float32")

    return top_left, top_right, bottom_right, bottom_left

def rectify_monitor(image, top_left, top_right, bottom_right, bottom_left):
    """
    Warp the detected monitor to a front-facing rectangle.
    """
    # NOTE: In this example, the order of four corner points (top left, top right, bottom left, bottom_right) is provided.
    #       In the actual competition, you should find the order of the corner points by yourself.

    width_top = np.linalg.norm(top_right - top_left)
    width_bottom = np.linalg.norm(bottom_right - bottom_left)
    max_width = int(max(width_top, width_bottom))

    height_right = np.linalg.norm(bottom_right - top_right)
    height_left = np.linalg.norm(bottom_left - top_left)
    max_height = int(max(height_right, height_left))

    src = np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")

    dst = np.array(
        [
            [0,0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    transform = cv2.getPerspectiveTransform(src, dst)

    rectified = cv2.warpPerspective(
        image,
        transform,
        (max_width, max_height),
    )

    return rectified

def detect_line(rectified):
    """
    Detect the line inside the rectified monitor.
    """
    gray = cv2.cvtColor(rectified, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    margin_ratio = 0.05
    margin_x = int(w * margin_ratio)
    margin_y = int(h * margin_ratio)
    
    valid_region = gray[
        margin_y:h - margin_y,
        margin_x:w - margin_x,
    ]
    
    black_list = []
    iteration = 20
    threshold = 1

    valid_h, valid_w = valid_region.shape
    for y in range(valid_h):
        for x in range(valid_w):
            if valid_region[y, x] < 20:
                black_list.append((x + margin_x, y + margin_y))

    n = len(black_list)
    max_inlier = []

    for i in range(iteration):
        inlier = []

        idx1, idx2 = np.random.choice(n, 2, False)

        x1, y1 = black_list[idx1]
        x2, y2 = black_list[idx2]

        if abs(x2 - x1) < 1e-6:
            continue

        a = float((y2-y1)/(x2-x1)) # TODO
        b = -a*x1+y1 # TODO
        if a is None or b is None:
            continue

        for x, y in black_list:
            if line_point_distance(a, b, x, y) < threshold:
                inlier.append((x,y))

        if len(inlier) > len(max_inlier):
            max_inlier = inlier

    if len(max_inlier) < 2:
        return None
    
    a, b = fit_line(max_inlier)
    if a is None or b is None:
        return None

    inliers = np.array(max_inlier, dtype=np.float32)

    x_min = int(np.min(inliers[:,0]))
    x_max = int(np.max(inliers[:,0]))

    y_min = int(a * x_min + b)
    y_max = int(a * x_max + b)

    y_min = max(0, min(h - 1, y_min))
    y_max = max(0, min(h - 1, y_max))

    best_line = (x_min, y_min, x_max, y_max)

    return best_line

def calculate_angle(line):
    if line is None:
        return None
    
    x1, y1, x2, y2 = line
        
    dx = x2-x1 # TODO
    dy = -1*(y2-y1) # TODO

    angle = np.degrees(np.arctan2(dy,dx)) # TODO
    # Hint: np.degrees(np.arctan2(???, ???))

    # TODO: np.arctan2 returns asn angle in the range (-180, 180] degrees.
    #       Convert the angle so that the output is in the range (-90, 90].
    if (0<angle<=180):
        angle-=90
    else:
        angle+=90

    #angle = None # TODO

    return angle

def line_point_distance(a, b, x, y):
        
    distance = float(abs(a*x-y+b)/np.sqrt(a*a+1)) # TODO

    return distance

def fit_line(points_list):

    num_a,den_a,x_bar,y_bar=0,0,0,0
    n=len(points_list)

    for i in range(n):
        x,y=points_list[i]
        x_bar+=x
        y_bar+=y
    x_bar=x_bar/n
    y_bar=y_bar/n

    for i in range(n):
        x,y=points_list[i]
        num_a+=(x-x_bar)*(y-y_bar)
        den_a+=(x-x_bar)**2

    a=num_a/den_a
    b=y_bar-a*x_bar

    return a, b
