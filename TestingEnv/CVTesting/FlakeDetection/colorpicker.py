#!/usr/bin/env python3
"""
Color Picker Tool
Hover over an image to see the RGB/BGR color values of pixels in real-time.
"""

import cv2
import numpy as np
import sys
import os


class ColorPicker:
    def __init__(self, image_path):
        """
        Initialize the color picker with an image.
        
        Args:
            image_path: Path to the image file
        """
        # Load image
        self.image_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if self.image_bgr is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to RGB for display
        self.image_rgb = cv2.cvtColor(self.image_bgr, cv2.COLOR_BGR2RGB)
        
        # Create a copy for displaying
        self.display_image = self.image_bgr.copy()
        
        # Current mouse position
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Window name
        self.window_name = "Color Picker - Press 'q' to quit, 's' to save coordinates"
        
    def mouse_callback(self, event, x, y, flags, param):
        """
        Mouse callback function to track mouse movement.
        """
        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_x = x
            self.mouse_y = y
            
            # Update display
            self.update_display()
    
    def update_display(self):
        """
        Update the display image with color information overlay.
        """
        # Create a copy of the original image
        display = self.image_bgr.copy()
        
        # Get pixel color values
        if (0 <= self.mouse_x < self.image_bgr.shape[1] and 
            0 <= self.mouse_y < self.image_bgr.shape[0]):
            
            # BGR values (OpenCV format)
            bgr = self.image_bgr[self.mouse_y, self.mouse_x]
            b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
            
            # RGB values
            rgb = self.image_rgb[self.mouse_y, self.mouse_x]
            r_rgb, g_rgb, b_rgb = int(rgb[0]), int(rgb[1]), int(rgb[2])
            
            # Draw crosshair
            cv2.line(display, (self.mouse_x - 20, self.mouse_y), 
                    (self.mouse_x + 20, self.mouse_y), (0, 255, 0), 1)
            cv2.line(display, (self.mouse_x, self.mouse_y - 20), 
                    (self.mouse_x, self.mouse_y + 20), (0, 255, 0), 1)
            
            # Draw a small square showing the color
            color_square_size = 30
            color_square = np.zeros((color_square_size, color_square_size, 3), dtype=np.uint8)
            color_square[:, :] = [b, g, r]  # BGR for OpenCV
            display[10:10+color_square_size, 10:10+color_square_size] = color_square
            
            # Draw border around color square
            cv2.rectangle(display, (10, 10), (10+color_square_size, 10+color_square_size), 
                         (255, 255, 255), 2)
            
            # Prepare text information
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 1
            line_height = 20
            y_offset = 50
            
            # Background for text (semi-transparent)
            text_bg_height = 120
            overlay = display.copy()
            cv2.rectangle(overlay, (10, y_offset - 5), (350, y_offset + text_bg_height), 
                         (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
            
            # Text color (white)
            text_color = (255, 255, 255)
            
            # Display information
            info_lines = [
                f"Position: ({self.mouse_x}, {self.mouse_y})",
                f"BGR: ({b}, {g}, {r})",
                f"RGB: ({r_rgb}, {g_rgb}, {b_rgb})",
                f"Hex RGB: #{r_rgb:02X}{g_rgb:02X}{b_rgb:02X}",
                f"Hex BGR: #{b:02X}{g:02X}{r:02X}",
            ]
            
            for i, line in enumerate(info_lines):
                y_pos = y_offset + i * line_height
                cv2.putText(display, line, (15, y_pos), font, font_scale, text_color, thickness)
            
            # Update display
            self.display_image = display
    
    def run(self):
        """
        Run the color picker application.
        """
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Initial display
        self.update_display()
        
        print("Color Picker started!")
        print("Instructions:")
        print("  - Move mouse over image to see pixel colors")
        print("  - Press 'q' to quit")
        print("  - Press 's' to save current pixel coordinates and color")
        print("  - Press 'r' to reset display")
        
        while True:
            # Show image
            cv2.imshow(self.window_name, self.display_image)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save current pixel info
                if (0 <= self.mouse_x < self.image_bgr.shape[1] and 
                    0 <= self.mouse_y < self.image_bgr.shape[0]):
                    bgr = self.image_bgr[self.mouse_y, self.mouse_x]
                    rgb = self.image_rgb[self.mouse_y, self.mouse_x]
                    print(f"\nSaved pixel info:")
                    print(f"  Position: ({self.mouse_x}, {self.mouse_y})")
                    print(f"  BGR: ({bgr[0]}, {bgr[1]}, {bgr[2]})")
                    print(f"  RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})")
            elif key == ord('r'):
                # Reset display
                self.display_image = self.image_bgr.copy()
                self.update_display()
        
        cv2.destroyAllWindows()
        print("Color Picker closed.")


def main():
    """
    Main function to run the color picker.
    """
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python colorpicker.py <image_path>")
        print("\nExample:")
        print("  python colorpicker.py images/image4.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
    
    try:
        # Create and run color picker
        picker = ColorPicker(image_path)
        picker.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

