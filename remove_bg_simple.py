from PIL import Image

def remove_background(input_path, output_path, threshold=200):
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        # Check if pixel is light (part of checkerboard)
        # Average brightness or all channels > threshold
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0)) # Make transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved background-removed image to {output_path}")

remove_background("team logo.jpeg", "team_logo_transparent.png")
