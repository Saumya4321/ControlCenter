from pathlib import Path
import easygui
import os

input_directory = easygui.diropenbox(title="Select Input Folder")

if input_directory:
    input_path = Path(input_directory) # convert into Path object

    for file in input_path.iterdir():
        if file.is_file():
            old_name = file.stem         
            ext = file.suffix            

            i = len(old_name) - 1
            while i >= 0 and old_name[i].isdigit():
                i -= 1

            base_name = old_name[:i+1]     
            number_part = old_name[i+1:]   

            if number_part:  
                new_number = str(int(number_part))  
                new_name = base_name + new_number
            else:
                new_name = old_name  # fallback

            new_file_path = file.with_name(new_name + ext)

            print(f"Renaming {file.name} → {new_file_path.name}")

            os.rename(file, new_file_path)
else:
    print("No folder selected.")
