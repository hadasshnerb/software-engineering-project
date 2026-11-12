# Topic Proposal: Facilitating Matches on Allocation Platforms

## 1. Project Information

**Course:** Software Engineering, 7030910, Semester A, 2026–2027

**Team members:** Hadas Raviv and Shaked Horesh

**Topic:** Assigning courses to classrooms through suggested constraint relaxations

## 2. Project Summary and Problem

We study an allocation system in which courses request classrooms, and each course may have classrooms that are more or less suitable. The original allocation system uses a fixed algorithm. A facilitator suggests that agents relax some constraints to increase the number of assigned courses, while protecting agents who have been guaranteed a resource and staying within a defined relaxation budget.

We will implement Algorithm 1 from the paper **Facilitating Matches on Allocation Platforms** and compare it with allocation without relaxations and an ILP formulation. The project will examine when the suggestions improve the allocation, what they cost, and how their runtime compares with the alternatives.

## 3. Research Questions

1. How does the relaxation budget affect the number of assigned courses and the cost of relaxations?
2. At what instance sizes does ILP runtime become significant, and does Algorithm 1 remain practical?
3. How does demand relative to capacity affect the performance of each method?

## 4. Model Definition

### Input and Output

- **Agents:** Courses requesting assignments.
- **Resources:** Available classrooms. If the data includes time slots, each classroom–time-slot pair will be treated as a resource so that a classroom cannot be assigned to overlapping courses.
- **Input data:** Courses, classrooms, allowed matches, match attributes and relaxation costs, the relaxation budget, and guarantee rules.
- **Output:** Course-to-classroom assignments, the selected relaxation suggestions, and outcome metrics. Unassigned requests and cases with no valid solution will be reported explicitly.

### Graphs and Relaxation Costs

- \(E\) — edges representing matches that require no relaxation.
- \(E_r\) — potential match edges enabled by a relaxation, with a cost for each relaxation. Costs will be defined in advance based on data attributes, such as classroom capacity or distance, and documented.
- \(E'\) — relaxation suggestions selected by the paper's method.
- After selecting suggestions, we will run a maximum bipartite matching algorithm on the expanded graph.

We will precisely define what counts as one relaxation, how its cost is calculated, what the relaxation budget limits, and what constitutes a guarantee that must not be violated. These definitions will follow the paper's formulation; any adaptation or simplification will be documented.

### Objective and Constraints

- **Primary objective:** Maximize the number of assigned courses.
- **Hard constraints:** Each course is assigned at most once; each resource is used by at most one course in each relevant time slot; assignments use only allowed matches or selected relaxations; the relaxation budget is not exceeded; and all specified guarantees are preserved.
- **Preferences:** Matches requiring relaxations are less desirable than original matches. We will measure the actual relaxation cost separately from the number of assignments.
- **Information assumption:** All requests and resources are known before execution, unless review of the paper leads us to choose otherwise. Any difference between this assumption and the paper's setting will be stated explicitly.

## 5. Allocation Methods for Comparison

1. **Baseline without relaxations:** Maximum matching using only \(E\).
2. **Algorithm 1:** The paper's method for selecting relaxation suggestions, using the specified guarantee rule and budget. A maximum matching will then be run on the expanded graph.
3. **ILP:** An optimization formulation of the same model, using the same inputs, constraints, budget, and guarantees. The report will explain the decision variables, objective function, and treatment of costs.

We may also present an upper bound or additional reference scenarios, such as allocation without guarantees. These will be reported as separate reference metrics and will not replace the fair comparison among the three methods.

## 6. Data and Instance Generation

**Preferred source:** Course and classroom data from Ariel University, subject to approval and access to data that may be used and shared as required. Identifying information will be removed, and the processing steps will be documented.

**Alternative:** Fis0506-1 instances from the ITC 2007 benchmark, [itc2007-cct](https://github.com/Docheinstein/itc2007-cct). Before using this data, we will inspect the available fields, verify that conversion to the course–classroom model is valid, and document the conversion rules. If synthetic data is used to extend the experiments, we will document the data generator, distributions, and random seeds. Synthetic data will not be the sole data source if suitable public or real-world data can be obtained.

## 7. Experimental Design

All methods will run on the same instances, under the same constraints and with the same metric definitions. We will test at least three experimental variables, each at three levels:

1. **Relaxation budget:** Low, medium, and high, with ranges defined relative to the costs in the instances.
2. **Demand load:** Low, medium, and high, based on the ratio between the number of requests and available capacity.
3. **Instance size:** Small, medium, and large, based on the number of courses and resources.

The numerical values for each level will be determined and reported after inspecting the data. If a method or instance-generation process is randomized, we will run at least 10 independent trials per configuration, record seeds and run parameters, and report the mean and a measure of variation. Repeating an identical deterministic run on a fixed input is unnecessary.

### Metrics

- Number and percentage of courses assigned.
- Total relaxation cost and average relaxation cost per assigned course.
- Number or percentage of guarantees preserved; violating a hard guarantee will count as a validity failure.
- Runtime in seconds.
- Percentage of instances for which a valid solution was found, with failures or cases with no solution reported explicitly.

### Results Presentation

- Percentage of assigned courses as a function of the relaxation budget.
- Percentage of assigned courses as a function of demand load.
- Runtime as a function of instance size.
- Where relevant, relaxation cost versus the number of assigned courses.

Every table or chart will include labeled axes, units, a legend, the number of trials, and measures of variation. We will analyze when each method succeeds or struggles, the trade-offs between allocation and cost, and at least one result that was unexpected or revealed a limitation. We will not infer from the tested instances that a method is generally optimal.

## 8. Software Architecture and Execution Workflow

1. **Data loading and processing:** Load and validate the input, then convert it to the model's unified representation.
2. **Instance construction:** Build \(E\), \(E_r\), relaxation costs, and parameters.
3. **Method execution:** Run the Baseline, Algorithm 1, and ILP on the same instance.
4. **Solution validation:** Independently check assignment constraints, the relaxation budget, and guarantees.
5. **Measurement and storage:** Calculate metrics and save results, parameters, and seeds in a structured file.
6. **Analysis:** Generate tables and charts from the result files.

We will separate data loading, allocation logic, solution validation, metric calculation, and result presentation as much as possible. The report will include a brief component diagram and describe each component's responsibility.

## 9. Correctness Tests

- A small example with an expected solution calculated and checked manually.
- Tests that no course or resource is assigned more than once and that every match satisfies the model's rules.
- Tests that the relaxation budget and guarantees are preserved.
- Edge cases: empty input, insufficient resources, a course with no compatible resource, and an instance in which no relaxations are possible.
- Every experimental output will be validated before metrics are calculated. Invalid outputs and cases with no solution will be reported explicitly rather than counted as successful results.

## 10. Milestones and Deliverables

1. **Topic proposal:** A description of the problem, paper, planned model and methods, and possible data sources.
2. **Design and initial implementation:** Model definition, component diagram, hand-worked example, Baseline, and initial tests.
3. **Experiments and analysis:** Run the methods, save results, generate charts, and analyze findings and limitations.
4. **Submission and presentation:** Runnable code, a README with installation and execution instructions, input files or instructions for obtaining them, results, chart-generation scripts, a final report in English, and a presentation.

The report will also describe team member contributions, limitations, sources, and the use of AI tools and how their outputs were checked. The presentation will demonstrate sample input and output, explain the paper and model, show a central result and at least one limitation, and give each team member a substantial part.

## 11. Decisions to Confirm Before Full Implementation

- Select the data source and confirm permissions for its use.
- Define the data-to-model mapping, including time-slot representation if relevant.
- Specify the paper's guarantee, relaxation-budget, and relaxation-cost definitions.
- Set numerical values for the three experimental levels of each variable.
- Finalize the ILP formulation and define any results used as bounds or reference scenarios.
