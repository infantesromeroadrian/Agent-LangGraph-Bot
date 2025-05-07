#!/usr/bin/env python
"""Generate a workflow diagram image from ASCII art."""
import os
from PIL import Image, ImageDraw, ImageFont

# Configuration
FONT_SIZE = 14
CHAR_WIDTH = 10
CHAR_HEIGHT = 20
PADDING = 20
BG_COLOR = (255, 255, 255)  # White
TEXT_COLOR = (0, 0, 0)  # Black
OUTPUT_FILE = "workflow.png"

def generate_image_from_ascii(ascii_file_path, output_path):
    """Generate an image from ASCII art file.
    
    Args:
        ascii_file_path: Path to the ASCII art file
        output_path: Path to save the output image
    """
    # Read ASCII content
    with open(ascii_file_path, 'r') as f:
        lines = f.readlines()
    
    # Calculate image dimensions
    width = max(len(line) for line in lines) * CHAR_WIDTH + 2 * PADDING
    height = len(lines) * CHAR_HEIGHT + 2 * PADDING
    
    # Create image
    img = Image.new('RGB', (width, height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Try to load a monospace font
    try:
        font = ImageFont.truetype("Courier", FONT_SIZE)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw ASCII art
    y_position = PADDING
    for line in lines:
        draw.text((PADDING, y_position), line, fill=TEXT_COLOR, font=font)
        y_position += CHAR_HEIGHT
    
    # Save the image
    img.save(output_path)
    print(f"Generated workflow diagram: {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ascii_file = os.path.join(script_dir, "workflow.txt")
    output_file = os.path.join(script_dir, OUTPUT_FILE)
    
    if os.path.exists(ascii_file):
        generate_image_from_ascii(ascii_file, output_file)
    else:
        print(f"Error: ASCII file not found at {ascii_file}") 