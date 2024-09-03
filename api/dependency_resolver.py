import os
import sys

reference_module_paths = [
    './',  
    './config',  
    './lsl',  
    './media',  
    './misc',  
    './src',  
]

for module_path in reference_module_paths:
    reference_path = os.path.abspath(module_path)
    sys.path.append(reference_path)
