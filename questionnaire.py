# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(page_title="Engineering Criticality Assessment", layout="wide")

# ----------------------------
# Helpers
# ----------------------------
def init_state():
    if "register" not in st.session_state:
        st.session_state.register = pd.DataFrame(columns=[
            "Asset ID", "Asset Description", "Area / Line", "Assessor", "Date",
            "Safety risk override",
            "PF1 Typical failure interval", "PF2 Duty", "PF3 Load", "PF4 Environment",
            "CF1 Consequential damage (1-20)", "CF2 Stop of critical line", "CF3 Cost of failure", "CF4 Time to repair",
            "DT Failure observable/detectable",
            "PF (overall)", "CF (overall)", "RPN (PF x CF x DT)", "Critical (safety override)"
        ])

def clear_form():
    # Keep register; clear only inputs
    for k in list(st.session_state.keys()):
        if k.startswith("f_"):
            del st.session_state[k]

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Register")
    out.seek(0)
    return out.read()

init_state()

# ----------------------------
# UI Header
# ----------------------------
st.markdown("## Engineering Criticality Assessment – Data Entry")

# Right-side action buttons (mimic screenshot)
top_left, top_right = st.columns([4, 1])
with top_right:
    if st.button("CLEAR DATA", use_container_width=True):
        clear_form()
        st.rerun()

# ----------------------------
# Form + Calculations
# ----------------------------
with st.form("criticality_form", clear_on_submit=False):
    # Asset details block
    c1, c2, c3 = st.columns([1.1, 1.1, 1.1])
    with c1:
        asset_id = st.text_input("Asset ID", key="f_asset_id")
        asset_desc = st.text_input("Asset Description", key="f_asset_desc")
    with c2:
        area_line = st.text_input("Area / Line", key="f_area_line")
        assessor = st.text_input("Assessor", key="f_assessor")
    with c3:
        assess_date = st.date_input("Date", value=date.today(), key="f_date")
        safety_override = st.selectbox(
            "Safety risk / risk of injury if failure occurs?",
            options=["No", "Yes"],
            key="f_safety_override"
        )

    st.markdown("---")

    st.markdown("### Probability factors (PF) — score each 1–10")
    pf_col1, pf_col2 = st.columns([1.2, 1.2])
    with pf_col1:
        pf1 = st.slider(
            "PF1 – Typical failure interval (1–10)",
            1, 10, 5,
            help="Low: monthly–never (1–3); Medium: weekly–monthly (4–7); High: daily (8–10)",
            key="f_pf1"
        )
        pf2 = st.slider(
            "PF2 – Duty (1–10)",
            1, 10, 5,
            help="Part-time (1–5) … Full-time / non-stop (6–10)",
            key="f_pf2"
        )
    with pf_col2:
        pf3 = st.slider(
            "PF3 – Load (1–10)",
            1, 10, 5,
            help="Low predictable (1–3) … Medium design load (4–7) … High unpredictable (8–10)",
            key="f_pf3"
        )
        pf4 = st.slider(
            "PF4 – Environment (1–10)",
            1, 10, 5,
            help="Light clean (1–3) … Medium factory (4–7) … Harsh wet/dirty (8–10)",
            key="f_pf4"
        )

    st.markdown("---")
    st.markdown("### Consequence factors (CF)")
    cf_col1, cf_col2 = st.columns([1.2, 1.2])
    with cf_col1:
        cf1 = st.slider(
            "CF1 – Consequential damage (1–20)",
            1, 20, 5,
            help="No secondary damage (1–5). Yes: could damage other components or cause contamination (10–20).",
            key="f_cf1"
        )
        cf2 = st.slider(
            "CF2 – Stop of critical line (1–10)",
            1, 10, 5,
            help="No (1–5). Yes: stops critical line/plant (6–10).",
            key="f_cf2"
        )
    with cf_col2:
        cf3 = st.slider(
            "CF3 – Cost of failure (1–10)",
            1, 10, 5,
            help="Low (1–3) … Medium (4–7) … High (8–10).",
            key="f_cf3"
        )
        cf4 = st.slider(
            "CF4 – Time to repair (1–10)",
            1, 10, 5,
            help="Low 0–30 min (1–3) … Medium 30–240 min (4–7) … High > same day (8–10).",
            key="f_cf4"
        )

    st.markdown("---")
    st.markdown("### Detectability (DT) — score 1–10")
    dt = st.slider(
        "DT – Failure observable/detectable (1–10)",
        1, 10, 5,
        help="Low: automated alarms (1–3); Medium: chance/random (4–7); High: unlikely/undetectable (8–10)",
        key="f_dt"
    )

    # Calculations
    pf_overall = round((pf1 + pf2 + pf3 + pf4) / 4, 2)

    # CF1 is 1–20 on the sheet; convert to a 1–10 equivalent for the overall CF calculation
    cf1_equiv = cf1 / 2.0  # 1..10
    cf_overall = round((cf1_equiv + cf2 + cf3 + cf4) / 4, 2)

    rpn = round(pf_overall * cf_overall * dt, 2)
    critical = "Yes" if safety_override == "Yes" else "No"

    st.markdown("---")
    st.markdown("### Calculated results")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("PF (overall)", f"{pf_overall}")
    r2.metric("CF (overall)", f"{cf_overall}")
    r3.metric("RPN (PF × CF × DT)", f"{rpn}")
    r4.metric("Critical (safety override)", critical)

    submit = st.form_submit_button("SUBMIT / UPDATE", use_container_width=True)

if submit:
    new_row = {
        "Asset ID": asset_id,
        "Asset Description": asset_desc,
        "Area / Line": area_line,
        "Assessor": assessor,
        "Date": str(assess_date),
        "Safety risk override": safety_override,
        "PF1 Typical failure interval": pf1,
        "PF2 Duty": pf2,
        "PF3 Load": pf3,
        "PF4 Environment": pf4,
        "CF1 Consequential damage (1-20)": cf1,
        "CF2 Stop of critical line": cf2,
        "CF3 Cost of failure": cf3,
        "CF4 Time to repair": cf4,
        "DT Failure observable/detectable": dt,
        "PF (overall)": pf_overall,
        "CF (overall)": cf_overall,
        "RPN (PF x CF x DT)": rpn,
        "Critical (safety override)": critical,
    }
    st.session_state.register = pd.concat(
        [st.session_state.register, pd.DataFrame([new_row])],
        ignore_index=True
    )
    st.success("Saved to register.")

# ----------------------------
# Register + Download
# ----------------------------
st.markdown("---")
st.markdown("## Register")

reg = st.session_state.register.copy()
if not reg.empty:
    reg = reg.sort_values(by="RPN (PF x CF x DT)", ascending=False)
st.dataframe(reg, use_container_width=True, hide_index=True)

col_a, col_b = st.columns([1, 3])
with col_a:
    excel_bytes = to_excel_bytes(reg)
    st.download_button(
        "Download register (Excel)",
        data=excel_bytes,
        file_name="engineering_criticality_register.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_b:
    st.caption(
        "Note: CF1 is captured as 1–20 per your sheet, but is converted to a 1–10 equivalent (CF1/2) "
        "when calculating CF (overall), so PF/CF/DT stay comparable."
    )