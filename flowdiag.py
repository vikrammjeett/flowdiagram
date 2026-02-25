import streamlit as st

DEBUG = False

# Define the decision flow in one place
FLOW = {
    "stop_critical_machine_check": {
        "question": "Does the component failure stop a critical machine?",
        "yes": "critical",
        "no": "inhibit_safety_check",
    },
    "inhibit_safety_check": {
        "question": "Does it inhibit a safety system?",
        "yes": "critical",
        "no": "stop_production_check",
    },
    "stop_production_check": {
        "question": "Does it stop a production line?",
        "yes": "critical",
        "no": "not_critical",
    },
}

TERMINALS = {"critical", "not_critical"}

# Initialize state
if "step" not in st.session_state:
    st.session_state.step = "stop_critical_machine_check"

# Debug view + reset
top = st.columns([1, 1, 3])
with top[0]:
    if st.button("Reset", use_container_width=True):
        st.session_state.step = "stop_critical_machine_check"
        st.rerun()
with top[1]:
    DEBUG = st.toggle("Debug", value=DEBUG)

if DEBUG:
    st.write("Current step:", st.session_state.step)

step = st.session_state.step

# Terminal steps
if step == "critical":
    st.info("Component is critical")
elif step == "not_critical":
    st.info("Component is NOT critical")

# Question steps
else:
    node = FLOW.get(step)
    if node is None:
        st.error(f"Unknown step: {step}")
        st.stop()

    st.write(node["question"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes", key=f"{step}_yes", use_container_width=True):
            st.session_state.step = node["yes"]
            st.rerun()
    with c2:
        if st.button("No", key=f"{step}_no", use_container_width=True):
            st.session_state.step = node["no"]
            st.rerun()