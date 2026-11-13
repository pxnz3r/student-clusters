"""
groups.py - names and advice for the student groups.

The algorithms only return group numbers. Each group is named from its
averages with the rules below, written once, so the same students always
get the same name.
"""

from student_clusters.data import ATTENDANCE

ABSENT = "Absent"
DROPPING_OFF = "Dropping off"
STEADY = "Steady"
ENGAGED = "Highly engaged"

ADVICE = {
    ABSENT: "Contact in the first weeks: they barely log in and hand in almost nothing, and most withdraw.",
    DROPPING_OFF: "Follow up after the first missed assignment: they start, then stop about halfway.",
    STEADY: "Study skills support: they hand in nearly everything, yet about three in ten fail.",
    ENGAGED: "Stretch material: they log in almost every week and most pass, many with distinction.",
}


def group_name(attendance):
    """
    Name a group from its average attendance. Attendance, study activity
    and assignment completion rise together here, so attendance alone
    orders the groups.

    Input:
        attendance: the group's average attendance (0 to 1).
    Returns:
        A group name.
    """
    if attendance < 0.15:
        return ABSENT
    if attendance < 0.45:
        return DROPPING_OFF
    if attendance < 0.8:
        return STEADY
    return ENGAGED


def name_groups(students, labels):
    """
    A unique name for every group number ("Steady 2" if a name repeats).

    Inputs:
        students: the student table.
        labels: the group of each student.
    Returns:
        Dictionary group number -> name.
    """
    means = students[ATTENDANCE].groupby(labels).mean()
    names = {}
    for group, attendance in means.items():
        name = group_name(attendance)
        repeats = sum(value == name or value.startswith(name + " ") for value in names.values())
        names[int(group)] = name if repeats == 0 else f"{name} {repeats + 1}"
    return names


def advice_for(name):
    """
    The advice for a group name ("Steady 2" uses Steady).

    Input:
        name: a name from name_groups().
    Returns:
        The advice.
    """
    base = name.rstrip("0123456789 ")
    return ADVICE.get(base, "")
