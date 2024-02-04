import json
import os

from eta import HKEta

hketa = HKEta()


def coverage():
    directory = "times"
    counter = 0

    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    counter += len(data)
            except json.JSONDecodeError as e:
                print(f"Error reading {filename}: {e}")

    percentage = (counter / len(hketa.stop_list)) * 100
    with open("coverage.txt", 'w') as file:
        file.write(f"{percentage:.2f}%")


if __name__ == '__main__':
    coverage()
