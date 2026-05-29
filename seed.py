# basically the purpose of this is like
# creating courses.json and students.json

# to create the file: run python seed.py
# requirement: already have data folder

import json
import os

def write_json(path, data):
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"written -> {path}")


def main():
    print("reading seed_data.json...")

    with open("seed_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    courses = data["courses"]
    students = data["students"]

    write_json("data/courses.json", courses)
    write_json("data/students.json", students)

    print("\ndone!")
    print("next step: flask run")


if __name__ == "__main__":
    main()