# Simulation viewer

Open `viewer.html` in a browser and click **Load JSON** to select a saved
`Simulator.get_results()` JSON file. Load another file to switch simulations.

No Python command, server, installation, or internet connection is needed.
Files stay on your computer. The viewer is a source file in this folder,
not a generated output, and is not ignored by Git.

- **Visible duration**: zoom using whole time units.
- **Position**: move through the run using whole time units.
- **Marker legend**: expand or collapse the explanation of sN, dN, and !.
  Execution bars retain brief hover tooltips; no detail paragraph is shown.
- **Full run**: click the overview to move the visible window.
- **Export SVG**: download the current timeline window and overview as a standalone
  vector image, including scheduler name, configuration, and selected time range.
  The exported background is transparent, with dark text, light grid lines, and
  a fixed palette suitable for white/light paper backgrounds, independent of the viewer theme.
  Task labels have a left margin and execution bars have softly rounded corners.

The summary displays the scheduler name and configuration instead of task/cycle counts.

Axis labels are integers; source timestamps in details are preserved.

Idle intervals use a neutral gray fill and show an “Idle” label when space permits. The first six
tasks keep the base palette; additional task rows receive generated hues instead
of repeating the six colors. Colors remain consistent between the main chart and
overview within a loaded run. With many tasks, use row names and cycle details
as well as color: arbitrarily many colors cannot remain visually distinct.

**Export PNG** downloads the same view with transparency and paper-friendly colors.
It uses 2× resolution, reduced automatically for large charts to stay within canvas
size limits. SVG remains preferable when unlimited vector scaling is needed.

Deadline: expected cycle arrival + period. For period zero, use expected arrival
+ requested `burst_time` (not actual execution duration). Completion exactly at
the deadline is on time; the final cycle also has a deadline.

Metrics include `deadline_miss_count` and `average_deadline_miss_time` overall
and per task. The average includes only missed cycles and is zero if none miss.
Each cycle includes `deadline`, `deadline_missed`, and `deadline_miss_time`.
Task definitions must be present for every completed task.
The viewer shows dashed deadline markers labeled d0, d1, etc.; red markers
with ! indicate misses. Markers are included in SVG and PNG exports.

Expected-start markers (`s0`, `s1`, …) use scheduled arrival times. Separate
Expected starts and Deadlines buttons toggle each marker type, including in
exports. Missed deadline labels are red; marker lines stay neutral. Coincident
starts and deadlines share a line with both labels.

## Overall results comparison

Open `results_viewer.html` in a browser (keep `results_viewer.js` beside it).
Click **Load metrics JSONs** and select one or more saved `calculate_metrics(results)`
reports, such as `simulation_metrics.json`. Loading more files adds runs to the
comparison. Each run has a consistent color; scheduler configuration appears
alongside its name. Use × to remove a run, or **Clear all** to start again.

- **Direct values** shows six separate charts for context switches, average
  turnaround, response, waiting, missed-deadline count, and average deadline miss
  time. The table below provides numeric values. Cycle counts appear beside runs.
- **Improvement ±%** lets you select a baseline and shows the other runs using
  `(baseline − result) / baseline × 100`. Positive means lower/better, negative
  means higher/worse. Zero against zero is 0%; a nonzero result against a zero
  baseline, or an undefined metric, is N/A. Hover table cells for the raw values.

New metrics reports preserve `scheduler` and `task_input_hash` from the simulation
output. Regenerate older reports to include this information. Older reports still
load using filenames as labels, with an unverified-input notice. Different known
hashes or cycle counts block percentage comparisons; direct values remain available.
Average deadline miss time still averages only missed cycles, so read it together
with the missed-deadline count. No per-task or per-cycle graphs are shown.

This viewer works offline without a server or dependencies and does not upload files.

Result plots use colors without repeated scheduler names. The shared legend shows
full names and configurations, wrapping long labels. Hover a bar or row color
marker to identify its run; color markers also identify zero and N/A values.

### Export comparison charts

Each chart has **SVG** and **PNG** buttons for a single-chart download. Use
**Include in export** checkboxes (or **Select all / Select none**) to choose multiple
charts, then **Export selected SVG/PNG**. **One image** combines the selected charts
into one vertically stacked image with a shared legend. **Separate files** downloads
one image per selected chart; browsers may request permission for multiple downloads.

Exports preserve the active direct/improvement mode, baseline, colors, metric
values and input-comparison notices. Full scheduler names wrap in the legend;
names are not repeated on bars. The background is transparent, with dark text
for white/light paper backgrounds. PNG uses up to 2× resolution, capped at 8192
pixels per dimension and 16 million pixels; SVG stays vector at any size.
