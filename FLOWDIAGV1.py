import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="FMEA Light • Component Criticality", page_icon="🛠️", layout="centered")

# -----------------------------
# Example dropdown data (replace with your real lists / register)
# -----------------------------
LINES = ["Line 1", "Line 2", "Line 3"]

MACHINES_BY_LINE = {
    "Line 1": ["Mixer A", "Conveyor 1", "Sealer X"],
    "Line 2": ["Conveyor 2", "Weigher B", "Labeler Z"],
    "Line 3": ["Oven 1", "Chiller 1", "Conveyor 3"],
}

COMPONENTS_BY_MACHINE = {
    "Mixer A": ["Motor", "Gearbox", "Seal", "Bearing"],
    "Conveyor 1": ["Belt", "Motor", "Drive roller", "Sensor"],
    "Sealer X": ["Heater", "Thermocouple", "Relay", "Air cylinder"],
    "Conveyor 2": ["Belt", "Motor", "Sensor"],
    "Weigher B": ["Load cell", "Controller", "Cable"],
    "Labeler Z": ["Printhead", "Stepper motor", "Encoder"],
    "Oven 1": ["Burner", "Fan motor", "Thermostat"],
    "Chiller 1": ["Compressor", "Evap fan", "Expansion valve"],
    "Conveyor 3": ["Belt", "Motor", "Sensor"],
}

# -----------------------------
# Decision flow (single source of truth)
# -----------------------------
FLOW = {
    "stop_critical_machine_check": {
        "title": "Critical machine impact",
        "question": "Does the component failure stop a critical machine?",
        "yes": "critical",
        "no": "inhibit_safety_check",
    },
    "inhibit_safety_check": {
        "title": "Safety impact",
        "question": "Does it inhibit a safety system?",
        "yes": "critical",
        "no": "stop_production_check",
    },
    "stop_production_check": {
        "title": "Production impact",
        "question": "Does it stop a production line?",
        "yes": "critical",
        "no": "not_critical",
    },
}
ORDER = list(FLOW.keys())
TERMINALS = {"critical", "not_critical"}


# -----------------------------
# Helpers
# -----------------------------
def safe_filename(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    return s or "export"


def reset_all():
    st.session_state.stage = "inputs"
    st.session_state.step = ORDER[0]
    st.session_state.trace = []
    st.session_state.line = None
    st.session_state.machine = None
    st.session_state.component = None
    st.session_state.want_download = False


def build_excel_bytes() -> io.BytesIO:
    # Summary row
    summary = pd.DataFrame(
        [
            {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Line": st.session_state.line,
                "Machine": st.session_state.machine,
                "Component": st.session_state.component,
                "Result": st.session_state.step,
            }
        ]
    )

    # Trace sheet
    trace_df = pd.DataFrame(
        [
            {
                "Step": i,
                "Question Step": t["question_step"],
                "Question": t["question"],
                "Answer": t["answer"],
                "Next Step": t["next_step"],
            }
            for i, t in enumerate(st.session_state.trace, 1)
        ]
    )

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        trace_df.to_excel(writer, index=False, sheet_name="Decision Trace")
    buf.seek(0)
    return buf


# -----------------------------
# State init
# -----------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "inputs"  # inputs -> tree

if "step" not in st.session_state:
    st.session_state.step = ORDER[0]

if "trace" not in st.session_state:
    st.session_state.trace = []

for k in ["line", "machine", "component"]:
    if k not in st.session_state:
        st.session_state[k] = None

if "want_download" not in st.session_state:
    st.session_state.want_download = False


# -----------------------------
# Header / Reset
# -----------------------------
left, right = st.columns([3, 1])
with left:
    st.subheader("FMEA Light")
    st.write("Component criticality decision flow")
with right:
    if st.button("Reset", use_container_width=True):
        reset_all()
        st.rerun()

# Sidebar decision trace
st.sidebar.subheader("Decision trace")
if st.session_state.trace:
    for i, t in enumerate(st.session_state.trace, 1):
        st.sidebar.write(f"**{i}.** {t['question']}")
        st.sidebar.write(f"→ {t['answer']}")
else:
    st.sidebar.write("No decisions yet.")

# -----------------------------
# Stage 1: Inputs
# -----------------------------
if st.session_state.stage == "inputs":
    st.markdown("### Select asset context")

    # Line
    line_choice = st.selectbox(
        "Line",
        options=["Select..."] + LINES,
        index=0 if st.session_state.line is None else 1 + LINES.index(st.session_state.line),
    )
    if line_choice == "Select...":
        st.session_state.line = None
        st.session_state.machine = None
        st.session_state.component = None
    else:
        if st.session_state.line != line_choice:
            st.session_state.line = line_choice
            st.session_state.machine = None
            st.session_state.component = None

    # Machine (filtered by line)
    machines = MACHINES_BY_LINE.get(st.session_state.line, [])
    machine_choice = st.selectbox(
        "Machine",
        options=["Select..."] + machines,
        index=0 if st.session_state.machine is None else 1 + machines.index(st.session_state.machine),
        disabled=st.session_state.line is None,
    )
    if machine_choice == "Select...":
        st.session_state.machine = None
        st.session_state.component = None
    else:
        if st.session_state.machine != machine_choice:
            st.session_state.machine = machine_choice
            st.session_state.component = None

    # Component (filtered by machine)
    components = COMPONENTS_BY_MACHINE.get(st.session_state.machine, [])
    component_choice = st.selectbox(
        "Component",
        options=["Select..."] + components,
        index=0 if st.session_state.component is None else 1 + components.index(st.session_state.component),
        disabled=st.session_state.machine is None,
    )
    if component_choice == "Select...":
        st.session_state.component = None
    else:
        st.session_state.component = component_choice

    ready = all([st.session_state.line, st.session_state.machine, st.session_state.component])

    st.markdown("---")
    if st.button("Start decision tree", use_container_width=True, disabled=not ready):
        st.session_state.stage = "tree"
        st.session_state.step = ORDER[0]
        st.session_state.trace = []
        st.session_state.want_download = False
        st.rerun()

    if ready:
        st.caption(
            f"Selected: Line **{st.session_state.line}** | Machine **{st.session_state.machine}** | Component **{st.session_state.component}**"
        )

# -----------------------------
# Stage 2: Decision tree
# -----------------------------
else:
    step = st.session_state.step

    st.caption(
        f"Line: {st.session_state.line}  •  Machine: {st.session_state.machine}  •  Component: {st.session_state.component}"
    )

    # Progress indicator
    if step in ORDER:
        idx = ORDER.index(step) + 1
        st.progress(idx / len(ORDER), text=f"Step {idx} of {len(ORDER)}")
    else:
        st.progress(1.0, text="Complete")

    # Terminal screens + optional Excel download
    if step in TERMINALS:
        if step == "critical":
            st.success("Result: Component is CRITICAL")
        else:
            st.info("Result: Component is NOT critical")

        st.markdown("---")
        st.session_state.want_download = st.radio(
            "Do you want to download this as an Excel document?",
            options=["No", "Yes"],
            horizontal=True,
            index=1 if st.session_state.want_download else 0,
        ) == "Yes"

        if st.session_state.want_download:
            xlsx = build_excel_bytes()
            fname = (
                f"{safe_filename(st.session_state.line)}_"
                f"{safe_filename(st.session_state.machine)}_"
                f"{safe_filename(st.session_state.component)}_criticality.xlsx"
            )
            st.download_button(
                label="Download Excel",
                data=xlsx,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True):
                # Go back to last asked question
                if st.session_state.trace:
                    last = st.session_state.trace.pop()
                    st.session_state.step = last["question_step"]
                else:
                    st.session_state.step = ORDER[0]
                st.session_state.want_download = False
                st.rerun()
        with c2:
            if st.button("Change machine/component", use_container_width=True):
                st.session_state.stage = "inputs"
                st.session_state.step = ORDER[0]
                st.session_state.trace = []
                st.session_state.want_download = False
                st.rerun()

    # Question screens
    else:
        node = FLOW.get(step)
        if node is None:
            st.error(f"Unknown step: {step}")
            st.stop()

        st.markdown(f"### {node['title']}")
        st.write(node["question"])

        choice = st.radio(
            "Answer",
            options=["Yes", "No"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"{step}_choice",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True, disabled=(len(st.session_state.trace) == 0 and step == ORDER[0])):
                if st.session_state.trace:
                    last = st.session_state.trace.pop()
                    st.session_state.step = last["question_step"]
                else:
                    st.session_state.step = ORDER[0]
                st.rerun()

        with c2:
            if st.button("Next", use_container_width=True):
                next_step = node["yes"] if choice == "Yes" else node["no"]
                st.session_state.trace.append(
                    {
                        "question_step": step,
                        "question": node["question"],
                        "answer": choice,
                        "next_step": next_step,
                    }
                )
                st.session_state.step = next_step
                st.rerun()

        st.markdown("---")
        if st.button("Change machine/component", use_container_width=True):
            st.session_state.stage = "inputs"
            st.session_state.step = ORDER[0]
            st.session_state.trace = []
            st.session_state.want_download = False
            st.rerun()
