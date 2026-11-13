# Methodology

## Question

Do students fall into distinct learning patterns by attendance, study time and assignment completion? Do hierarchical clustering and K-Means find the same patterns, and do the patterns say anything about how students end up?

## Data

The Open University Learning Analytics Dataset (OULAD) records 32,593 students of seven online courses in 2013 and 2014. One course presentation is used: module DDD, autumn 2014, 38 weeks with six tutor-marked assignments. Students who unregistered before the course began are dropped, leaving 1,655. `scripts/build_students.py` reduces each student to one row:

| Input | Built from |
| --- | --- |
| Attendance | weeks with at least one visit to the online learning environment / 38 |
| Study activity | clicks in the learning environment / 38 weeks |
| Assignment completion | tutor-marked assignments submitted / 6 |

The Open University teaches at a distance, so attendance means logging in to the course website rather than sitting in a classroom, and study time is measured by activity on it. The final result (distinction, pass, fail, withdrawn) is kept aside and only used to check the groups.

Study activity is very skewed (median 12 clicks a week, top 1% over 140), so it is clustered as log10(1 + clicks); on the raw scale a handful of heavy users would form a group of their own. All three inputs are then standardised.

## Methods

**Hierarchical (agglomerative) clustering** starts with each student alone and repeatedly merges the two closest groups until one is left. The linkage decides what "closest groups" means:

| Linkage | Distance between two groups |
| --- | --- |
| Ward | how much merging them increases the spread inside groups |
| Average | mean distance between their members |
| Complete | largest distance between their members |
| Single | smallest distance between their members |

Cutting the merge tree (dendrogram) at a height gives k groups.

**K-Means** places k centres, gives every student to the nearest, moves each centre to the mean of its students, and repeats until nothing changes; 20 random starts, seed 42.

Groups are renumbered by average attendance and named with fixed rules: below 15% "Absent", below 45% "Dropping off", below 80% "Steady", otherwise "Highly engaged".

## Choosing k

k = 2 has the best silhouette for both methods but only splits active from inactive students. k is chosen from 3 to 6 by K-Means stability: the adjusted Rand index between 10 single-start runs from different seeds. k = 4 scores 0.99 (lowest pair 0.97). The same k is used for both methods so their groups can be compared.

## Checks

1. Final results per group, which neither method saw.
2. The four linkages at k = 4: silhouette and group sizes.
3. Ward against K-Means: a cross-table and the adjusted Rand index.

## Limits

- One course presentation; other courses may show other patterns.
- Clicks measure activity on the course website, not time spent studying offline.
- Withdrawn students stop generating activity when they leave, so part of their low attendance follows from withdrawing rather than causing it. The groups describe patterns; they don't prove causes.
