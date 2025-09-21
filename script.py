import cv2
import numpy as np
import os

# --- Configuration ---
FILLED_BUBBLE_THRESHOLD = 0.6  # Threshold for filled bubble detection
ADAPTIVE_THRESH_BLOCK_SIZE = 15  # Increased block size for adaptive thresholding
ADAPTIVE_THRESH_C = 4  # Slightly increased constant for adaptive thresholding
MIN_INITIAL_AREA = 50  # Lowered to match updated code and capture smaller bubbles

def compute_dynamic_area_thresholds(contours, min_aspect_ratio=0.65, max_aspect_ratio=1.38):
    """
    Compute dynamic BUBBLE_MIN_AREA and BUBBLE_MAX_AREA based on contour areas.
    """
    areas = []
    for c in contours:
        area = cv2.contourArea(c)
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        # Broad initial filter to include potential bubbles
        if MIN_INITIAL_AREA < area < 2000 and min_aspect_ratio <= aspect_ratio <= max_aspect_ratio:
            areas.append(area)
    
    if not areas:
        print("Warning: No contours found for dynamic area calculation. Using fallback values.")
        return 250, 800
    
    # Compute median and IQR
    areas = np.array(areas)
    median_area = np.median(areas)
    q1 = np.percentile(areas, 25)
    q3 = np.percentile(areas, 75)
    iqr = q3 - q1
    
    # Set thresholds as median ± 1.5 * IQR, with reasonable bounds
    min_area = max(100, median_area - 1.5 * iqr)
    max_area = min(2000, median_area + 1.5 * iqr)
    
    print(f"Dynamic Area Thresholds: BUBBLE_MIN_AREA = {min_area:.1f}, BUBBLE_MAX_AREA = {max_area:.1f}")
    return min_area, max_area

def process_with_fallback(image_path):
    """
    Resizes the image to a target height of 1000 pixels and marks filled bubbles with red circles using contour-based logic.
    """
    # Validate image path
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}. Please check the path or format.")
        return None
    
    # Proper resize to target height of 1000 pixels while maintaining aspect ratio
    ratio = 1000.0 / image.shape[0]
    new_width = int(image.shape[1] * ratio)
    image = cv2.resize(image, (new_width, 1000), interpolation=cv2.INTER_AREA)
    
    # Mark filled bubbles with red circles after resizing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, ADAPTIVE_THRESH_BLOCK_SIZE, ADAPTIVE_THRESH_C
    )

    # Save thresholded image for debugging
    cv2.imwrite("debug_thresholded.jpg", thresh)
    print("Saved thresholded image as 'debug_thresholded.jpg'")

    # Find and filter bubble contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    BUBBLE_MIN_AREA, BUBBLE_MAX_AREA = compute_dynamic_area_thresholds(contours)
    
    bubble_contours = []
    for c in contours:
        area = cv2.contourArea(c)
        if BUBBLE_MIN_AREA < area < BUBBLE_MAX_AREA:
            (x, y, w, h) = cv2.boundingRect(c)
            aspect_ratio = w / float(h)
            if 0.75 <= aspect_ratio <= 1.25:  # Relaxed aspect ratio range
                bubble_contours.append(c)

    print(f"Detected {len(bubble_contours)} potential bubbles after filtering.")
    if not bubble_contours:
        print("Warning: No bubbles found to process.")
    
    vis_resized = image.copy()
    for c in bubble_contours:
        (x, y, w, h) = cv2.boundingRect(c)
        center_x, center_y = x + w//2, y + h//2
        radius = max(w, h)//2
        
        # Draw green circle for all detected bubbles
        cv2.circle(vis_resized, (center_x, center_y), radius, (0, 255, 0), 2)
        
        # Check if bubble is filled using fill ratio
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)
        masked_thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
        filled_pixels = cv2.countNonZero(masked_thresh)
        total_pixels = cv2.countNonZero(mask)
        fill_ratio = filled_pixels / float(total_pixels) if total_pixels > 0 else 0
        
        # Mark filled bubbles with red circle if fill ratio exceeds threshold
        if fill_ratio > FILLED_BUBBLE_THRESHOLD:
            cv2.circle(vis_resized, (center_x, center_y), radius, (0, 0, 255), 2)
    
    # Display images with consistent window sizes
  
    cv2.imshow("04 - Resized with Marked Bubbles", cv2.resize(vis_resized, (600, 750)))
    cv2.waitKey(0)
    
    return None

# --- Main execution ---
if __name__ == "__main__":
    # for i in range(1, 24):
    #     image_file = f""
    #     print(f"\n--- Processing {image_file} ---")
    #     process_with_fallback(image_file)
    #     cv2.destroyAllWindows()
    image_file = "Img1.jpeg"
    print(f"\n--- Processing {image_file} ---")
    process_with_fallback(image_file)
    cv2.destroyAllWindows()