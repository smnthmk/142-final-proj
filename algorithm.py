def buildGraduationPlan(course_data, student_data):
    semester_order = ["1st", "2nd", "midyear"]

    courses = course_data

    course_map = {}
    adjacency_list = {}
    in_degree = {}

    # store each course in a map for easier access
    for course in courses:
        code = course["course_code"]

        course_map[code] = {
            "course_code": code,
            "name": course.get("name", ""),
            "semester_availability": course.get("semester_availability", ["1st", "2nd", "midyear"]),
            "year_level": course["year_level"],
            "prerequisites": course.get("prerequisites", [])
        }

        # initialize graph values
        adjacency_list[code] = []
        in_degree[code] = 0

    # build graph where prereq points to the course that needs it
    for course in courses:
        code = course["course_code"]

        for prereq in course.get("prerequisites", []):
            if prereq not in adjacency_list:
                adjacency_list[prereq] = []

            adjacency_list[prereq].append(code)
            in_degree[code] += 1

    completed = set(student_data.get("completed_courses", []))
    in_progress = set(student_data.get("in_progress_courses", []))

    # assume current in progress courses will be completed after this sem
    completed.update(in_progress)

    remaining = set()

    # only include courses that are not yet completed
    for course in courses:
        code = course["course_code"]

        if code not in completed:
            remaining.add(code)

    current_semester = student_data.get("semester", "1st")

    # start planning from the next semester
    if current_semester in semester_order:
        semester_index = semester_order.index(current_semester) + 1
    else:
        semester_index = 0

    # checks if all prereqs are already completed
    def prerequisitesCompleted(course):
        for prereq in course["prerequisites"]:
            if prereq not in completed:
                return False
        return True

    # checks if the course is offered in the current semester
    def offeredThisSemester(course, semester):
        return semester in course["semester_availability"]

    semester_buckets = []
    safety_counter = 0
    max_iterations = len(courses) * len(semester_order) * 2

    # keep scheduling until no course is left
    while len(remaining) > 0:
        current_semester = semester_order[semester_index % len(semester_order)]

        bucket = {
            "semester": current_semester,
            "courses": []
        }

        scheduled_this_semester = []

        # find courses that can be taken this semester
        for code in list(remaining):
            course = course_map[code]

            if (
                prerequisitesCompleted(course)
                and offeredThisSemester(course, current_semester)
            ):
                scheduled_this_semester.append(code)

        # add the scheduled courses to the semester bucket
        for code in scheduled_this_semester:
            course = course_map[code]

            bucket["courses"].append(course)
            remaining.remove(code)

        # mark scheduled courses as completed for the next semesters
        for code in scheduled_this_semester:
            completed.add(code)

            # reduce the in degree of courses that depend on this course
            for next_course in adjacency_list.get(code, []):
                in_degree[next_course] -= 1

        semester_buckets.append(bucket)

        # move to the next semester
        semester_index += 1
        safety_counter += 1

        # prevents infinite loop if some courses can never be scheduled
        if safety_counter > max_iterations:
            return {
                "success": False,
                "reason": "Some courses could not be scheduled. Possible causes: missing prerequisite, circular prerequisite, or seasonal conflict",
                "adjacency_list": adjacency_list,
                "in_degree": in_degree,
                "semester_buckets": semester_buckets,
                "unscheduled_courses": [
                    course_map[code] for code in remaining
                ]
            }

    # compute the projected year level and semester of graduation
    projected_graduation = computeProjectedGraduation(
        student_data.get("current_year", 1),
        student_data.get("semester", "1st"),
        semester_buckets
    )

    return {
        "success": True,
        "adjacency_list": adjacency_list,
        "in_degree": in_degree,
        "semester_buckets": semester_buckets,
        "projected_graduation": projected_graduation
    }


def computeProjectedGraduation(current_year, current_semester, semester_buckets):
    year = current_year
    semester = current_semester

    # go through each planned semester
    for bucket in semester_buckets:
        bucket_semester = bucket["semester"]

        # increase year level when the plan cycles back to 1st sem
        if bucket_semester == "1st" and semester in ["2nd", "midyear"]:
            year += 1

        semester = bucket_semester

    return {
        "year_level": year,
        "semester": semester_buckets[-1]["semester"]
    }