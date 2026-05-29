import json
from graph import study_plan_graph

with open("data/courses.json") as f:
    courses = json.load(f)

# Using Zerzion's profile — a 2nd year student mid-curriculum
completed = [
    "CMSC 10", "CMSC 11", "CMSC 56", "Math 18", "COMM 10",
    "Math 53", "CMSC 57", "CMSC 21", "Math 54", "CMSC 123",
    "Physics 71", "Physics 71.1", "CMSC 22"
]

in_progress = [
    "CMSC 127", "CMSC 142", "CMSC 126", "CMSC 130"
]

planned = [
    "CMSC 128", "CMSC 131", "CMSC 124"
]

path = study_plan_graph(courses, completed, in_progress, planned)
print("Generated:", path)
print("Open static/course_graph.html in your browser.")