# Simulation viewer

Open `viewer.html` in a browser and click **Load JSON** to select a saved
`Simulator.get_results()` JSON file. Load another file to switch simulations.

No Python command, server, installation, or internet connection is needed.
Files stay on your computer. The viewer is a source file in this folder,
not a generated output, and is not ignored by Git.

- **Visible duration**: zoom using whole time units.
- **Position**: move through the run using whole time units.
- **Inspect visible interval**: show task, cycle, execution, and arrival details.
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
