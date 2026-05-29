import os
from pyvis.network import Network

STATUS_COLOR = {
    "completed":    "#B4FFB6",  # already completed
    "in_progress":  "#FFE599",  # currently taking
    "planned":      "#ABD9FF",  # planned to take
    "future":       "#FFA9A3",  # prereq met, but planned not to take
    "locked":       "#9E9E9E",  # prereq not met
}


def _status(code, prereqs, completed, in_progress, planned):

    if code in completed:
        return "completed"

    if code in in_progress:
        return "in_progress"

    if code in planned:
        return "planned"

    eligible_courses = completed | in_progress | planned
    if all(p in eligible_courses for p in prereqs):
        return "future"

    return "locked"


def study_plan_graph(courses, completed_courses, in_progress_courses, planned_courses):

    completed = set(completed_courses)
    in_progress = set(in_progress_courses)
    planned = set(planned_courses)

    all_subjects = {c["course_code"] for c in courses}

    net = Network(
        height="620px",
        width="100%",
        directed=True,  # arrows show prerequisite direction
        bgcolor="#ffffff",
        font_color="#000000",
        notebook=False,
        cdn_resources="in_line",  # embed vis.js inside the HTML (no internet needed)
    )

    net.set_options("""
                    {
                    "layout": {
                        "hierarchical": {
                        "enabled": true,
                        "direction": "UD",
                        "sortMethod": "directed",
                        "nodeSpacing": 200,
                        "levelSeparation": 100,
                        "blockShifting": true,
                        "edgeMinimization": true,
                        "parentCentralization": true,
                        "shakeTowards": "roots"
                        }
                    },
                    "physics": {
                        "enabled": false
                    },
                    "edges": {
                        "arrows": { "to": { "enabled": true, "scaleFactor": 0.7 } },
                        "color":  { 
                            "color": "#000000",
                            "hover": "#09FF00"},
                        "smooth": { "type": "cubicBezier" }
                    },
                    "interaction": {
                        "hover": true,
                        "tooltipDelay": 80,
                        "navigationButtons": true
                    }
                    }
                    """)

    # adding nodes
    for course in courses:
        code = course["course_code"]
        name = course.get("name", "")
        prereqs = course.get("prerequisites", [])

        status = _status(code, prereqs, completed, in_progress, planned)
        color = STATUS_COLOR[status]

        prereq_text = ", ".join(prereqs) if prereqs else "None"

        tooltip = (
            f"{code}\n"
            f"{name}\n\n"
            f"Status: {status.replace('_', ' ').title()}\n"
            f"Prerequisites: {prereq_text}"
        )

        net.add_node(
            code,
            label=code,
            title=tooltip,
            color={
                "background": color,
                "border": "#333333",
                "highlight": {
                    "background": color,
                    "border": "#ffff00",
                },
            },
            shape="box",              # rectangle shape
            widthConstraint=130,      # fixed width
            font={"size": 11, "color": "#000000"},
        )

        # adding edges

    for course in courses:
        code = course["course_code"]
        prereqs = course.get("prerequisites", [])

        for prereq in prereqs:

            if prereq in all_subjects:
                net.add_edge(prereq, code, width=1.5)

    os.makedirs("static", exist_ok=True)
    output_path = "static/course_graph.html"
    html = net.generate_html(notebook=False)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path