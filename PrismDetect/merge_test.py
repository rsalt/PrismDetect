from PIL import Image
import os

base_dir = "./data/references"
img1_path = os.path.join(base_dir, "test-product", "front.jpg")
img2_path = os.path.join(base_dir, "ghee-1liter", "ref_1771835323.jpg")

if os.path.exists(img1_path) and os.path.exists(img2_path):
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    
    # Resize to have same height for merging
    h = min(img1.height, img2.height)
    img1 = img1.resize((int(img1.width * h / img1.height), h))
    img2 = img2.resize((int(img2.width * h / img2.height), h))
    
    total_width = img1.width + img2.width
    new_im = Image.new('RGB', (total_width, h))
    
    new_im.paste(img1, (0,0))
    new_im.paste(img2, (img1.width, 0))
    
    output_path = "/tmp/multi_product_test.jpg"
    new_im.save(output_path)
    print(f"Saved merged image to {output_path}")
else:
    print("Could not find both reference images.")
