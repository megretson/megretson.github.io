import os

base_path = r"content/projects/quilts/30-30-30"
template = """+++
image = "grid.png"
date = "2025-01-{day:02d}"
title = "Var Gallery 30 x 30 x 30 Day {day}"
type = "gallery"
tags = ["personal", "artistic"]
summary = "Quilting projects"
+++
"""

# Create folders and index.md files
for day in range(1, 31):
    folder_name = f"day-{day}"
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, "index.md")
    with open(file_path, "w") as file:
        file.write(template.format(day=day))

print("Folders and index.md files created successfully!")