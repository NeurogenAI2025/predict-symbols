from PIL import Image

# Înlocuiește cu calea către fișierul tău PNG
input_file = "NeuroGen.png"
output_file = "favicon.ico"

# Deschide imaginea și salvează în format ICO
img = Image.open(input_file)
img.save(output_file, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
