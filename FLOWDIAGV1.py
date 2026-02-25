import streamlit as st

st.set_page_config(page_title="FMEA Light • Component Criticality", page_icon="🛠️", layout="centered")

# --- Example dropdown data (replace with your real lists) ---
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

# --- State init ---
if "stage" not in st.session_state:
    st.session_state.stage = "inputs"  # inputs -> tree/result

if "step" not in st.session_state:
    st.session_state.step = ORDER[0]

if "trace" not in st.session_state:
    st.session_state.trace = []

for k in ["line", "machine", "component"]:
    if k not in st.session_state:
        st.session_state[k] = None

# --- Header / Reset ---
left, right = st.columns([3, 1])
with left:
    st.subheader("FMEA Light")
    st.write("Component criticality decision flow")
with right:
    if st.button("Reset", use_container_width=True):
        st.session_state.stage = "inputs"
        st.session_state.step = ORDER[0]
        st.session_state.trace = []
        st.session_state.line = None
        st.session_state.machine = None
        st.session_state.component = None
        st.rerun()

# --- Sidebar trace (optional but useful) ---
st.sidebar.subheader("Decision trace")
if st.session_state.trace:
    for i, entry in enumerate(st.session_state.trace, 1):
        st.sidebar.write(f"**{i}.** {entry['question']}")
        st.sidebar.write(f"→ {entry['answer']}")
else:
    st.sidebar.write("No decisions yet.")

# =========================
# Stage 1: Inputs
# =========================
if st.session_state.stage == "inputs":
    st.markdown("### Select asset context")

    line = st.selectbox(
        "Line",
        options=["Select..."] + LINES,
        index=0 if st.session_state.line is None else (1 + LINES.index(st.session_state.line)),
    )
    if line == "Select...":
        st.session_state.line = None
        st.session_state.machine = None
        st.session_state.component = None
    else:
        if st.session_state.line != line:
            # line changed -> reset downstream
            st.session_state.line = line
            st.session_state.machine = None
            st.session_state.component = None

    machines = MACHINES_BY_LINE.get(st.session_state.line, [])
    machine = st.selectbox(
        "Machine",
        options=["Select..."] + machines,
        index=0 if st.session_state.machine is None else (1 + machines.index(st.session_state.machine)),
        disabled=st.session_state.line is None,
    )
    if machine == "Select...":
        st.session_state.machine = None
        st.session_state.component = None
    else:
        if st.session_state.machine != machine:
            st.session_state.machine = machine
            st.session_state.component = None

    components = COMPONENTS_BY_MACHINE.get(st.session_state.machine, [])
    component = st.selectbox(
        "Component",
        options=["Select..."] + components,
        index=0 if st.session_state.component is None else (1 + components.index(st.session_state.component)),
        disabled=st.session_state.machine is None,
    )
    if component == "Select...":
        st.session_state.component = None
    else:
        st.session_state.component = component

    ready = all([st.session_state.line, st.session_state.machine, st.session_state.component])

    st.markdown("---")
    if st.button("Start decision tree", use_container_width=True, disabled=not ready):
        st.session_state.stage = "tree"
        st.session_state.step = ORDER[0]
        st.session_state.trace = []
        st.rerun()

    if ready:
        st.caption(
            f"Selected: Line **{st.session_state.line}** | Machine **{st.session_state.machine}** | Component **{st.session_state.component}**"
        )

# =========================
# Stage 2: Decision tree
# =========================
else:
    step = st.session_state.step

    # Context banner
    st.caption(
        f"Line: {st.session_state.line}  •  Machine: {st.session_state.machine}  •  Component: {st.session_state.component}"
    )

    # Progress
    if step in ORDER:
        idx = ORDER.index(step) + 1
        st.progress(idx / len(ORDER), text=f"Step {idx} of {len(ORDER)}")
    else:
        st.progress(1.0, text="Complete")

    # Terminal states
    if step == "critical":
        st.success("Result: Component is CRITICAL")
    elif step == "not_critical":
        st.info("Result: Component is NOT critical")
    else:
        node = FLOW[step]
        st.markdown(f"### {node['title']}")
        st.write(node["question"])

        choice = st.radio(
            "Answer",
            ["Yes", "No"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"{step}_choice",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True):
                if st.session_state.trace:
                    st.session_state.trace.pop()
                    # Go back to previous question step (or start)
                    prev_step = ORDER[0]
                    if st.session_state.trace:
                        # We stored next_step; need to infer prior question step index
                        # simplest: walk forward from start using trace answers
                        prev_step = ORDER[0]
                        for t in st.session_state.trace[:-1]:
                            pass
                    st.session_state.step = ORDER[0] if not st.session_state.trace else ORDER[min(len(st.session_state.trace), len(ORDER)-1)]
                else:
                    st.session_state.step = ORDER[0]
                st.rerun()

        with c2:
            if st.button("Next", use_container_width=True):
                next_step = node["yes"] if choice == "Yes" else node["no"]

                st.session_state.trace.append({
                    "question_step": step,
                    "question": node["question"],
                    "answer": choice,
                    "next_step": next_step,
                })

                st.session_state.step = next_step
                st.rerun()

    # Optional: edit inputs without full reset
    st.markdown("---")
    if st.button("Change machine/component", use_container_width=True):
        st.session_state.stage = "inputs"
        st.session_state.step = ORDER[0]
        st.session_state.trace = []
        st.rerun()
