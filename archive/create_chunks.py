import os

# Filepath for the input JSONL file
input_file = "csm_data/batch/records.jsonl"

# Directory to store output chunks
output_dir = "csm_data/batch/jsonl_chunks"
os.makedirs(output_dir, exist_ok=True)

# Maximum chunk size in bytes (100MB)
max_chunk_size = 100 * 1024 * 1024  # 100 MB


def create_chunks(input_file, max_chunk_size, output_dir):
    with open(input_file, "r") as file:
        chunk_index = 0
        current_chunk_size = 0
        current_chunk = []

        for line in file:
            line_size = len(line.encode("utf-8"))  # Get the size of the line in bytes

            # Check if adding this line exceeds the max chunk size
            if current_chunk_size + line_size > max_chunk_size:
                # Write the current chunk to a new file
                chunk_filename = os.path.join(output_dir, f"chunk_{chunk_index}.jsonl")
                with open(chunk_filename, "w") as chunk_file:
                    chunk_file.writelines(current_chunk)

                print(
                    f"Created: {chunk_filename} ({current_chunk_size / (1024 * 1024):.2f} MB)"
                )

                # Reset for the next chunk
                chunk_index += 1
                current_chunk_size = 0
                current_chunk = []

            # Add the current line to the chunk
            current_chunk.append(line)
            current_chunk_size += line_size

        # Write the final chunk if it has data
        if current_chunk:
            chunk_filename = os.path.join(output_dir, f"chunk_{chunk_index}.jsonl")
            with open(chunk_filename, "w") as chunk_file:
                chunk_file.writelines(current_chunk)

            print(
                f"Created: {chunk_filename} ({current_chunk_size / (1024 * 1024):.2f} MB)"
            )


# Call the function to create chunks
create_chunks(input_file, max_chunk_size, output_dir)
