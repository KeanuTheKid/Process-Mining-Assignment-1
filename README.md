# Process Mining – Assignment 1

Analysis of the *Road Traffic Fine Management Process* event log (Process Mining, HSG, Fall 2026).

- `assignment1.py` – the marimo notebook (report)
- `assignment1.html` – static export, open in a browser without running anything

## Run it

The event log is not in the repo (185 MB). Download `Road_Traffic_Fine_Management_Process.xes.gz` from
[4TU.ResearchData](https://doi.org/10.4121/uuid:270fd440-1057-4fb9-89a9-b699b47990f5), unzip it into this folder, then:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/marimo edit assignment1.py
```
