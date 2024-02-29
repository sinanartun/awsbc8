import json

def process_links(file_path):
    url_to_remove = 'https://finans.mynet.com/borsa/hisseler/'

    # Read the data from the file
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Process the data to remove the unwanted part of the URLs
    for item in data:
        item[1] = item[1].replace(url_to_remove, '')

    # Write the processed data back to the file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Usage:
process_links('links.json')