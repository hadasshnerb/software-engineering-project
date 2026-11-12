# Facilitating Matches on Allocation Platforms

A Python project for comparing course-to-classroom allocation methods. It currently includes **Baseline**, an unweighted maximum-cardinality matching, and a project-adapted implementation of the paper's **Algorithm 1 (SNH-SB)**.

## Requirements

- Python 3.10 or later
- Install the NetworkX dependency with `python3 -m pip install -r requirements.txt`.

## Run

From the repository root, run both implemented algorithms on the included example:

```bash
python3 run_all.py
```

Choose one algorithm with `--algorithm baseline` or `--algorithm algorithm1`. For example:

```bash
python3 run_all.py --algorithm baseline
python3 run_all.py --algorithm algorithm1 --budget 1 --budget-mode size
```

Algorithm 1 accepts either a **size** budget (maximum number of recommendations) or a **discomfort** budget (maximum sum of recommendation costs). Size is the default. If omitted, the budget permits up to the maximum possible number of recommendations. The cost model is currently provisional; use `--budget-mode discomfort` only with that caveat in mind.

Provide another instance by specifying both CSV files:

```bash
python3 run_all.py --algorithm all \
  --courses path/to/courses.csv \
  --rooms path/to/rooms.csv
```

The command prints JSON containing each algorithm's assignments and unassigned requests. Algorithm 1 also reports its recommendations, budget, and summed recommendation cost.

## Input CSV format

The example files are in [`data/example/`](data/example/); their capacity values are synthetic and for demonstration only.

The layout follows the paper's separate course-group and classroom tables. Each row in `courses.csv` represents one meeting/request. `group_id` is the request ID when it appears once; repeated group IDs are treated as separate meetings and receive a row-order suffix. An optional `meeting_id` column can be supplied to set those suffixes explicitly. Each meeting is assigned independently.

`courses.csv` uses the requested columns:

| Column | Meaning |
|---|---|
| `group_id` | Course-group/request ID. |
| `code` | Course code. |
| `planned_registered_students` | Planned student count used to calculate the preferred capacity range. |
| `period`, `weekday`, `start_time`, `end_time` | Exact scheduled time slot. Times use 24-hour `HH:MM`. |

Each row represents one meeting. If a `group_id` repeats, meetings receive a row-order suffix in their internal request IDs. An optional `meeting_id` column can override these suffixes.

`rooms.csv` uses the requested columns: `classrooms_eng_id,Region,Building,Room,Capacity`. The room identity fields and capacity are used for allocation; region, building, and room number are retained as metadata. `Capacity` is the maximum number of students the room can hold.

The loader creates a separate room-time resource for every room and exact time slot in the course data. Meetings in the same period, weekday, and identical time range compete for the same room. A room may be reused at another time. This version does not treat partially overlapping but non-identical time ranges as conflicts.

For the capacity attribute, the loader follows the paper's preference bands: the preferred minimum is the planned student count rounded down to a multiple of 10; the preferred maximum is 4/3 of that count rounded down to a multiple of 10, capped at 270. Room capacity is likewise grouped into 10-seat bands. A room within the preferred range creates a compatible edge; each 10-seat band below the minimum or above the maximum adds one relaxation-cost unit. This project currently models capacity only, not the paper's region and accessibility preferences.

In this project, assigning a course to a room smaller than its planned student count is allowed and represented as a relaxable edge with a capacity discomfort cost. The cost bands are the current scoring assumption and should be replaced if the institution provides a specific penalty scale. Baseline computes an unweighted maximum-cardinality matching using only compatible edges; it does not calculate or optimize costs. The relaxation costs are available for Algorithm 1 and the ILP.

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Code structure

- [`src/models.py`](src/models.py) — allocation, meeting, and classroom domain models.
- [`src/data_loader.py`](src/data_loader.py) — `CourseDataLoader`.
- [`src/algorithms/baseline.py`](src/algorithms/baseline.py) — `BaselineMatcher`.
- [`src/algorithms/algorithm1.py`](src/algorithms/algorithm1.py) — project adapter for Algorithm 1 SNH-SB.
- [`src/validator.py`](src/validator.py) — independent matching, recommendation, and budget validation.
- [`src/experiments.py`](src/experiments.py) — experiment runners and result models.
- [`run_all.py`](run_all.py) — command-line entry point for one or all implemented algorithms.
- [`tests/`](tests/) — unit tests.
- [`third_party/facilitating-matches-paper/`](third_party/facilitating-matches-paper/) — pinned upstream research code as a Git submodule.

See [`DESIGN.md`](DESIGN.md) for the model, component diagram, worked example, and implementation plan. The original topic proposal is preserved in [`PROPOSAL.md`](PROPOSAL.md).

## Paper implementation

The authors' repository is included as a Git submodule at `third_party/facilitating-matches-paper/`, pinned to commit `7457b972c7d4b04b724abe916266b997a659be3d`. It retains the authors' MIT `LICENSE` and source history; do not remove the license or attribution when updating or reusing its code.

Clone this project with the submodule:

```bash
git clone --recurse-submodules <this-repository-url>
```

If you already cloned the project without submodules:

```bash
git submodule update --init --recursive
```

The upstream code is an experimental pipeline (`util.py`, preprocessing modules, and figure scripts), not a standalone package or a direct loader for our simplified course CSVs. Its helpers expect multidimensional preference/attribute data, while our input already provides a cost on each course-room pair. The integration in [`src/algorithms/algorithm1.py`](src/algorithms/algorithm1.py) adapts the paper's SNH-SB weighted-matching and dummy-agent procedure to this model, and uses NetworkX for maximum-weight and maximum-cardinality matching. It is not a direct invocation of the upstream figure scripts.
