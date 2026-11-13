### What this is

Grouping students by how they learn, with two clustering methods: **hierarchical clustering**, which keeps merging the two closest groups and records the merges as a tree, and **K-Means**, which moves k centres until every student sits with the nearest one. Nobody labelled the students; the algorithms find the groups.

The data is 1,655 real students of one Open University course (38 weeks, six assignments), from the Open University Learning Analytics Dataset. Three inputs:

- **Attendance**: share of course weeks in which the student opened the online learning environment.
- **Study activity**: clicks in the learning environment per week (clustered on a log scale).
- **Assignment completion**: share of the six assignments handed in.

### What to try

- **Explore**: switch between hierarchical clustering (with four linkages) and K-Means, and change k. The merge tree shows where the hierarchical cut falls.
- **Place a student**: enter a student's numbers and see their group and the advice for it.
- **Results**: how k was chosen, both groupings, and how they compare.

### What was found

| Group (K-Means) | Students | Attendance | Clicks per week | Assignments | Passed | Withdrew |
| --- | --- | --- | --- | --- | --- | --- |
| Highly engaged | 34% | 89% | 45 | 99% | 89% (15% distinction) | 2% |
| Steady | 31% | 61% | 12 | 93% | 56% | 13% |
| Dropping off | 18% | 24% | 6 | 46% | 2% | 63% |
| Absent | 17% | 5% | 1 | 4% | 0% | 81% |

- **Both methods find the same four groups.** Every student Ward calls absent or highly engaged, K-Means does too. They differ at the borders, mostly 192 students Ward calls steady and K-Means highly engaged.
- **The groups predict the final result**, which neither method saw: 81% of absent students withdrew; 89% of highly engaged ones passed.
- **Handing work in isn't enough.** Steady students submit 93% of assignments, yet 31% fail. They study online about a quarter as much as the engaged group (12 clicks a week against 45).
- **Linkage matters.** Ward gives four usable groups; single linkage chains everyone into one group of 1,651 and three stragglers.

Code and every figure: [github.com/pxnz3r/student-clusters](https://github.com/pxnz3r/student-clusters).
