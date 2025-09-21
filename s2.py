import cv2
import numpy as np
import os

from tilt import warp_image

# --- Configuration ---
FILLED_BUBBLE_THRESHOLD = 0.6
ADAPTIVE_THRESH_BLOCK_SIZE = 15
ADAPTIVE_THRESH_C = 4
MIN_INITIAL_AREA = 50

NUM_SUBJECTS = 5      # 5 columns (subjects)
NUM_OPTIONS = 4       # A, B, C, D
NUM_QUESTIONS = 20    # questions per subject

# -------------------------
# Helper functions
# -------------------------
def compute_dynamic_area_thresholds(contours, min_aspect_ratio=0.65, max_aspect_ratio=1.38):
    areas = []
    for c in contours:
        area = cv2.contourArea(c)
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        if MIN_INITIAL_AREA < area < 2000 and min_aspect_ratio <= aspect_ratio <= max_aspect_ratio:
            areas.append(area)
    
    if not areas:
        print("Warning: No contours found for dynamic area calculation. Using fallback values.")
        return 250, 800
    
    areas = np.array(areas)
    median_area = np.median(areas)
    q1 = np.percentile(areas, 25)
    q3 = np.percentile(areas, 75)
    iqr = q3 - q1
    
    min_area = max(100, median_area - 1.5 * iqr)
    max_area = min(2000, median_area + 1.5 * iqr)
    
    print(f"Dynamic Area Thresholds: BUBBLE_MIN_AREA = {min_area:.1f}, BUBBLE_MAX_AREA = {max_area:.1f}")
    return min_area, max_area

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]     
    rect[2] = pts[np.argmax(s)]     
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  
    rect[3] = pts[np.argmax(diff)]  
    return rect

# -------------------------
# Grid + extraction
# -------------------------
def compute_grid_layout(cropped_w, cropped_h,
                        q_row_weight=1.9, blank_row_weight=1.2,
                        option_col_weight=0.65, blank_col_weight=0.63,
                        edge_shrink_factor=1):
    """
    Compute precise grid layout:
    - Even columns (options + blanks) for each subject.
    - Even rows with 2 blank rows only between groups of 5 Qs.
    - Edge shrink applied symmetrically.
    """

    # --- counts ---
    groups = NUM_QUESTIONS // 5
    blank_row_blocks = groups - 1
    total_rows = NUM_QUESTIONS + blank_row_blocks * 2
    total_cols = NUM_SUBJECTS * NUM_OPTIONS + (NUM_SUBJECTS - 1) * 2

    # --- column weights ---
    widths = []
    for subj in range(NUM_SUBJECTS):
        # 4 options
        for _ in range(NUM_OPTIONS):
            widths.append(option_col_weight)
        # 2 blanks between subjects (not after last)
        if subj != NUM_SUBJECTS - 1:
            widths.extend([blank_col_weight, blank_col_weight])
    assert len(widths) == total_cols

    # --- row weights ---
    heights = []
    for group_idx in range(groups):
        heights.extend([q_row_weight] * 5)  # 5 questions
        if group_idx != groups - 1:
            heights.extend([blank_row_weight, blank_row_weight])
    assert len(heights) == total_rows

    # --- convert to arrays ---
    widths = np.array(widths, dtype=float)
    heights = np.array(heights, dtype=float)

    # --- shrink edges ---
    widths[0] *= edge_shrink_factor
    widths[-1] *= edge_shrink_factor
    heights[0] *= edge_shrink_factor
    heights[-1] *= edge_shrink_factor

    # --- rescale to exact size ---
    widths *= cropped_w / widths.sum()
    heights *= cropped_h / heights.sum()

    # --- integer rounding with remainder distribution ---
    def distribute(arr, target):
        arr_floor = np.floor(arr).astype(int)
        remainder = target - arr_floor.sum()
        if remainder > 0:
            fracs = arr - arr_floor
            for i in np.argsort(-fracs)[:remainder]:
                arr_floor[i] += 1
        return arr_floor

    widths_int = distribute(widths, cropped_w)
    heights_int = distribute(heights, cropped_h)

    return widths_int.tolist(), heights_int.tolist(), total_rows, total_cols



def visualize_grid(cropped_img):
    h, w = cropped_img.shape[:2]
    widths, heights, total_rows, total_cols = compute_grid_layout(w, h)

    vis = cropped_img.copy()

    # vertical (x) lines
    x = 0
    for cw in widths:
        cv2.line(vis, (x, 0), (x, h), (0, 255, 0), 1)
        x += cw
    cv2.line(vis, (x, 0), (x, h), (0, 255, 0), 1)

    # horizontal (y) lines
    y = 0
    for rh in heights:
        cv2.line(vis, (0, y), (w, y), (255, 0, 0), 1)
        y += rh
    cv2.line(vis, (0, y), (w, y), (255, 0, 0), 1)

    # cv2.imwrite("grid_visualization.jpg", vis)
    # cv2.imshow("Grid Visualization", cv2.resize(vis, (600, 900)))
    # print("Saved grid visualization as 'grid_visualization.jpg'")
    # cv2.waitKey(0)
    cv2.destroyAllWindows()

def extract_answers_from_cropped(cropped_vis, cropped_orig):
    h, w = cropped_vis.shape[:2]
    widths, heights, total_rows, total_cols = compute_grid_layout(w, h)

    # Map usable columns (skip blank gaps)
    col_to_subj_opt = {}
    col_counter = 0
    for subj in range(NUM_SUBJECTS):
        for opt in range(NUM_OPTIONS):
            col_to_subj_opt[col_counter] = (subj, opt)
            col_counter += 1
        if subj < NUM_SUBJECTS - 1:
            col_counter += 2  # blank spacing columns

    # Convert to HSV for red detection (highlighted circles)
    hsv = cv2.cvtColor(cropped_vis, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 120, 70]); upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 120, 70]); upper2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Answer storage
    answers = [["None"] * NUM_QUESTIONS for _ in range(NUM_SUBJECTS)]

    # Precompute grid positions
    cum_widths = np.cumsum([0] + widths)
    cum_heights = np.cumsum([0] + heights)

    # Loop over questions
    for q in range(1, NUM_QUESTIONS + 1):
        # Insert blank rows after every 5th question
        extra_rows_before = ((q - 1) // 5) * 2
        row_idx = (q - 1) + extra_rows_before

        if row_idx + 1 >= len(cum_heights):
            continue

        y1, y2 = int(cum_heights[row_idx]), int(cum_heights[row_idx + 1])
        y1, y2 = max(0, y1), min(h, y2)

        best_hits = {}
        for col in range(total_cols):
            if col not in col_to_subj_opt:
                continue
            x1, x2 = int(cum_widths[col]), int(cum_widths[col + 1])
            x1, x2 = max(0, x1), min(w, x2)

            if x2 <= x1 or y2 <= y1:
                continue

            roi = red_mask[y1:y2, x1:x2]
            red_pixels = int(cv2.countNonZero(roi))
            if red_pixels <= 0:
                continue

            subj, opt = col_to_subj_opt[col]
            prev = best_hits.get(subj, (None, 0))
            if red_pixels > prev[1]:
                best_hits[subj] = (opt, red_pixels)

        # Assign best option per subject
        for subj_idx in range(NUM_SUBJECTS):
            if subj_idx in best_hits:
                opt_idx = best_hits[subj_idx][0]
                answers[subj_idx][q - 1] = chr(65 + opt_idx)

                # Draw annotation
                chosen_col = [k for k, v in col_to_subj_opt.items() if v == (subj_idx, opt_idx)][0]
                cx1, cx2 = int(cum_widths[chosen_col]), int(cum_widths[chosen_col + 1])
                cy1, cy2 = y1, y2
                cv2.rectangle(cropped_vis, (cx1, cy1), (cx2, cy2), (0, 0, 255), 2)
                cv2.putText(cropped_vis, chr(65 + opt_idx),
                            (cx1 + 4, cy1 + (cy2 - cy1) // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Print results
    # for subj_idx in range(NUM_SUBJECTS):
    #     print(f"Subject {subj_idx+1} Answers:", answers[subj_idx])

    return answers, cropped_vis


# -------------------------
# Main
# -------------------------
def process_with_fallback(image_path_original):
    warpedImgLocation = warp_image(image_path_original)
    image_path = warpedImgLocation

    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}. Please check the path or format.")
        return None
    
    ratio = 1000.0 / image.shape[0]
    new_width = int(image.shape[1] * ratio)
    image = cv2.resize(image, (new_width, 1000), interpolation=cv2.INTER_AREA)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 51, 15)
    # cv2.imwrite("debug_thresholded.jpg", thresh)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    BUBBLE_MIN_AREA, BUBBLE_MAX_AREA = compute_dynamic_area_thresholds(contours)
    print("Bubble min and max area: ", BUBBLE_MIN_AREA, BUBBLE_MAX_AREA)
    print(f"Detected {len(contours)} total contours.")
    bubble_contours = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < BUBBLE_MIN_AREA*0.9 or area > BUBBLE_MAX_AREA*1.1:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        if not (0.5 <= aspect_ratio <= 1.5):
            continue
        perimeter = cv2.arcLength(c, True)
        if perimeter <= 0:
            continue
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        if circularity < 0.35:
            continue
        bubble_contours.append(c)

    print(f"Detected {len(bubble_contours)} potential bubbles after filtering.")
    vis_resized = image.copy()

    for c in bubble_contours:
        (x, y, w, h) = cv2.boundingRect(c)
        center_x, center_y = x + w//2, y + h//2
        radius = max(w, h)//2
        cv2.circle(vis_resized, (center_x, center_y), radius, (0, 255, 0), 2)
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)
        masked_thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
        filled_pixels = cv2.countNonZero(masked_thresh)
        total_pixels = cv2.countNonZero(mask)
        fill_ratio = filled_pixels / float(total_pixels) if total_pixels > 0 else 0
        if fill_ratio > FILLED_BUBBLE_THRESHOLD:
            cv2.circle(vis_resized, (center_x, center_y), radius, (0, 0, 255), 2)

    if bubble_contours:
        cropped_vis = vis_resized
        cropped_orig = image
        # cv2.imwrite("cropped_answer_region.jpg", cropped_vis)
        print("Saved cropped answer region as 'cropped_answer_region.jpg'")

        # show grid overlay for visual verification
        visualize_grid(cropped_vis)

        answers, annotated = extract_answers_from_cropped(cropped_vis, cropped_orig)
        for subj_idx, subj_answers in enumerate(answers, start=1):
            print(f"Subject {subj_idx}: {subj_answers}")
        # cv2.imwrite("annotated_extracted_answers.jpg", annotated)
        # cv2.imshow("Annotated Extracted Answers", cv2.resize(annotated, (600, 900)))
    else:
        print("No bubble contours found — cannot crop/extract.")
    # cv2.imshow("Detected Bubbles", cv2.resize(vis_resized, (600, 750)))
    # cv2.waitKey(0)
    cv2.destroyAllWindows()
    return answers if bubble_contours else None

# -------------------------
# Run
# -------------------------


if __name__ == "__main__":
    image_file = "Img1.jpeg"
    print(f"\n--- Processing {image_file} ---")
    answers = process_with_fallback(image_file)
    print("Final Answers:", answers)