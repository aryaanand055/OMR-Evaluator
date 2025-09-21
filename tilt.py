import cv2
import numpy as np
from sklearn.cluster import DBSCAN

def find_intersection(line1, line2):
    """Finds the intersection of two lines from cv2.fitLine."""
    vx1, vy1, x1, y1 = line1.flatten()
    vx2, vy2, x2, y2 = line2.flatten()
    den = vx1 * vy2 - vy1 * vx2
    if den == 0: return None
    t = ((x2 - x1) * vy2 - (y2 - y1) * vx2) / den
    px = x1 + t * vx1
    py = y1 + t * vy1
    return int(round(px)), int(round(py))


# Pass in the image to crop it
def warp_image(image_path):
    """
    The ultimate pipeline with hybrid detection for both circles and corners.
    """
    image = cv2.imread(image_path)
    if image is None: return None
    
    orig = image.copy()
    ratio = image.shape[0] / 1000.0
    image = cv2.resize(image, (int(image.shape[1] / ratio), 1000))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # cv2.imshow("01 - Resized Image", cv2.resize(image, (600, 750)))
    # cv2.waitKey(0)
    # cv2.imshow("02 - Grayscale", cv2.resize(gray, (600, 750)))
    # cv2.waitKey(0)
    
    centers = None
    MIN_CIRCLES_THRESHOLD = 50

    # === HYBRID BUBBLE DETECTION ===
    print("Attempting Method 1: HoughCircles...")
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=17,
        param1=50, param2=25, minRadius=9, maxRadius=15
    )

    if circles is not None and len(circles[0]) > MIN_CIRCLES_THRESHOLD:
        print(f"Success! Found {len(circles[0])} circles with HoughCircles.")
        centers = np.round(circles[0, :, :2]).astype("int")
        
        vis_hough = image.copy()
        for (x, y, r) in np.round(circles[0, :]).astype("int"):
            cv2.circle(vis_hough, (x, y), r, (0, 255, 0), 2)
        # cv2.imshow("03a - HoughCircles Detection", cv2.resize(vis_hough, (600, 750)))
        # cv2.waitKey(0)

    else:
        print("Method 1 failed. Falling back to robust method...")
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 51, 15)
        # cv2.imshow("03b - Adaptive Threshold", cv2.resize(thresh, (600, 750)))
        # cv2.waitKey(0)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vis_contours = image.copy()
        bubble_centers = []
        for c in contours:
            area = cv2.contourArea(c)
            perimeter = cv2.arcLength(c, True)
            if 50 < area < 500 and perimeter > 0:
                circularity = (4 * np.pi * area) / (perimeter * perimeter)
                if 0.8 < circularity < 1.2:
                    M = cv2.moments(c)
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    bubble_centers.append((cX, cY))
                    cv2.drawContours(vis_contours, [c], -1, (0, 255, 0), 2)
        
        if len(bubble_centers) > MIN_CIRCLES_THRESHOLD:
             print(f"Success! Found {len(bubble_centers)} bubbles with Contours.")
             centers = np.array(bubble_centers)
            #  cv2.imshow("04b - Contour Detection", cv2.resize(vis_contours, (600, 750)))
            #  cv2.waitKey(0)

    if centers is None:
        print("Both methods failed to find enough circles.")
        return None

    # === CLUSTERING STEP TO REMOVE NOISE ===
    clustering = DBSCAN(eps=90, min_samples=5).fit(centers) # Adjusted eps to be more balanced
    labels = clustering.labels_
    
    unique_labels, counts = np.unique(labels[labels != -1], return_counts=True)
    if len(counts) > 0:
        largest_cluster_label = unique_labels[np.argmax(counts)]
        centers = centers[labels == largest_cluster_label]
        print(f"Clustering complete. Isolated main grid with {len(centers)} bubbles.")

        vis_cluster = image.copy()
        for center in centers:
            cv2.circle(vis_cluster, tuple(center), 10, (0, 255, 0), 2)
        # cv2.imshow("04 - Clustered Bubbles (Noise Removed)", cv2.resize(vis_cluster, (600, 750)))
        # cv2.waitKey(0)

    # === START: HYBRID CORNER DETECTION ===
    tl, tr, bl, br = None, None, None, None
    try:
        # METHOD A: Try line-fitting (best for straight images)
        print("Attempting Corner Detection Method A: Line Fitting...")
        min_x, max_x = np.min(centers[:, 0]), np.max(centers[:, 0])
        min_y, max_y = np.min(centers[:, 1]), np.max(centers[:, 1])
        tolerance = 20

        left_circles = centers[centers[:, 0] < min_x + tolerance]
        right_circles = centers[centers[:, 0] > max_x - tolerance]
        top_circles = centers[centers[:, 1] < min_y + tolerance]
        bottom_circles = centers[centers[:, 1] > max_y - tolerance]
        
        left_line = cv2.fitLine(left_circles, cv2.DIST_L2, 0, 0.01, 0.01)
        right_line = cv2.fitLine(right_circles, cv2.DIST_L2, 0, 0.01, 0.01)
        top_line = cv2.fitLine(top_circles, cv2.DIST_L2, 0, 0.01, 0.01)
        bottom_line = cv2.fitLine(bottom_circles, cv2.DIST_L2, 0, 0.01, 0.01)

        tl = find_intersection(top_line, left_line)
        tr = find_intersection(top_line, right_line)
        bl = find_intersection(bottom_line, left_line)
        br = find_intersection(bottom_line, right_line)
        
        if not all([tl, tr, bl, br]): raise Exception("Line fitting failed to find all corners")
        print("Method A (Line Fitting) successful.")

    except Exception as e:
        # METHOD B: Fallback to tilt-robust method (best for skewed images)
        print(f"Method A failed ({e}), falling back to Method B (Tilt-Robust)...")
        s = centers.sum(axis=1)
        diff = centers[:, 0] - centers[:, 1]
        
        tl = tuple(centers[np.argmin(s)])
        br = tuple(centers[np.argmax(s)])
        tr = tuple(centers[np.argmax(diff)])
        bl = tuple(centers[np.argmin(diff)])
        print("Method B (Tilt-Robust) successful.")
    # === END: HYBRID CORNER DETECTION ===
    
    vis_lines = image.copy()
    cv2.line(vis_lines, tl, tr, (0, 0, 255), 2)
    cv2.line(vis_lines, tr, br, (0, 0, 255), 2)
    cv2.line(vis_lines, br, bl, (0, 0, 255), 2)
    cv2.line(vis_lines, bl, tl, (0, 0, 255), 2)
    for p in [tl, tr, br, bl]:
        cv2.circle(vis_lines, p, 10, (0, 255, 255), -1)
    # cv2.imshow("05 - Final Corners Detected", cv2.resize(vis_lines, (600, 750)))
    # cv2.waitKey(0)
    
    corner_points = np.array([tl, tr, br, bl], dtype="float32")
    corner_points *= ratio
    
    # === PERSPECTIVE TRANSFORM WITH MARGIN ===
    (tl_orig, tr_orig, br_orig, bl_orig) = corner_points
    widthA = np.sqrt(((br_orig[0] - bl_orig[0]) ** 2) + ((br_orig[1] - bl_orig[1]) ** 2))
    widthB = np.sqrt(((tr_orig[0] - tl_orig[0]) ** 2) + ((tr_orig[1] - tl_orig[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr_orig[0] - br_orig[0]) ** 2) + ((tr_orig[1] - br_orig[1]) ** 2))
    heightB = np.sqrt(((tl_orig[0] - bl_orig[0]) ** 2) + ((tl_orig[1] - bl_orig[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    padding_x = int(maxWidth * 0.02)
    padding_y = int(maxHeight * 0.02)
    
    dst = np.array([
        [padding_x, padding_y],
        [maxWidth + padding_x - 1, padding_y],
        [maxWidth + padding_x - 1, maxHeight + padding_y - 1],
        [padding_x, maxHeight + padding_y - 1]], dtype="float32")

    finalWidth = maxWidth + (2 * padding_x)
    finalHeight = maxHeight + (2 * padding_y)

    M = cv2.getPerspectiveTransform(corner_points, dst)
    warped = cv2.warpPerspective(orig, M, (finalWidth, finalHeight))
    
    # Save image as warped
    writeImg = "debug_warped.jpg"
    cv2.imwrite(writeImg, warped)
    # cv2.imshow("06 - Final Result with Margin", cv2.resize(warped, (600, 750)))
    cv2.waitKey(0)
    return writeImg

# --- Main execution ---
if __name__ == "__main__":
    image_file = "Img1.jpeg" # This one will now use Method A
    print(f"\n--- Processing {image_file} ---")
    final_sheet_name = warp_image(image_file)

    print(f"Saved warped image as {final_sheet_name}")

    
    cv2.destroyAllWindows()