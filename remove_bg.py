from rembg import remove
from PIL import Image

input_path = 'team logo.jpeg'
output_path = 'team_logo_transparent.png'

print(f"Opening {input_path}")
input_img = Image.open(input_path)

print(f"Removing background...")
output_img = remove(input_img)

print(f"Saving to {output_path}")
output_img.save(output_path)
print("Done")
