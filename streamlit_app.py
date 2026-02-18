import streamlit as st

if "step" not in st.session_state:
    st.session_state.step = "stop_critical_machine_check"
st.write("Current step:", st.session_state.step)

#decision logic
if st.session_state.step == "stop_critical_machine_check":
    st.write("Does the component failure stop a critical machine?")


    if st.button("Yes"):
        st.session_state.step = "Critical"
    
    if st.button("No"):
        st.session_state.step = "Inhibit_safety_check"

elif st.session_state.step == "Inhibit_safety_check":
    st.write("Does it inhibit a safety system?")

    if st.button("Yes"):
        st.session_state.step = "Critical"

    if st.button("No"):
        st.session_state.step = "Stop_production_check"
elif st.session_state.step == "Stop_production_check":
    st.write("Does it stop a production line?")
    if st.button("Yes"):
        st.session_state.step = "critical"
    if st.button("No"):
        st.session_state.step = "not_critical"
elif st.session_state.step == "critical":
    st.info("Component is critical")

elif st.session_state.step == "not_critical":
    st.info("Component is NOT critical.")