import os
import subprocess

def create_index_file(phase_encoding_file, index_file_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(index_file_path), exist_ok=True)

    # Read phase encoding directions and write index values to the index file
    with open(phase_encoding_file, 'r') as pe_file, open(index_file_path, 'w') as index_file:
        encoding_values = pe_file.read().strip().split(' ')
        # Assuming '2' is used for PA and '1' for AP in the phaseEncoding file
        index_values = ['2' if x == '-1' else '1' for x in encoding_values]
        index_file.write(' '.join(index_values) + '\n')


