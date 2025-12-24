import json
from datetime import datetime

import streamlit as st

from orchestrator import (
    STATE_PATH,
    load_state,
    save_state,
    step_content,
    step_pricing,
    step_research,
)


st.set_page_config(page_title="Agent Pipeline Control Panel", layout="wide")


def log_event(state, message: str, level: str = "info"):
    state.audit_log.append(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "stage": state.stage,
            "message": message,
        }
    )


def reset_pipeline(state, reason: str):
    updated = state.model_copy(deep=True)
    updated.research = None
    updated.pricing = None
    updated.content = None
    updated.stage = "INIT"
    log_event(updated, reason, level="warning")
    return updated


def persist_and_rerun(state):
    save_state(state)
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def display_json_block(title: str, payload):
    st.subheader(title)
    if payload is None:
        st.info("No data yet.")
    else:
        st.json(json.loads(payload.model_dump_json(indent=2)))


def main():
    st.title("Agent Pipeline Control Panel")
    st.caption(f"State file: {STATE_PATH}")

    state = load_state()

    with st.sidebar:
        st.subheader("Pipeline Controls")
        reset_clicked = st.button("Reset pipeline", type="primary")

        run_disabled = state.stage in {"HUMAN_REVIEW", "APPROVED", "REJECTED", "STOPPED", "CONTENT_DONE"}
        run_clicked = st.button("Run next step", disabled=run_disabled)

        if reset_clicked:
            updated_state = reset_pipeline(state, "Pipeline reset from UI")
            persist_and_rerun(updated_state)

        if run_clicked:
            try:
                if state.stage == "INIT":
                    updated_state = step_research(state)
                    log_event(updated_state, "Research step completed.")
                elif state.stage == "RESEARCH_DONE":
                    updated_state = step_pricing(state)
                    log_event(updated_state, "Pricing step completed.")
                elif state.stage == "PRICING_DONE":
                    updated_state = step_content(state)
                    log_event(updated_state, "Content step completed.")
                else:
                    updated_state = state
            except Exception as err:
                message = f"Error while running step: {err}"
                log_event(state, message, level="error")
                save_state(state)
                st.error(message)
            else:
                persist_and_rerun(updated_state)

    st.markdown(f"### Current stage: `{state.stage}`")

    editable_inputs = state.stage in {"INIT", "HUMAN_REVIEW"}
    with st.form("product_inputs"):
        st.subheader("Product inputs")
        product_name = st.text_input(
            "Product name", value=state.product_name, disabled=not editable_inputs
        )
        supplier_cost = st.number_input(
            "Supplier cost", value=float(state.supplier_cost), step=0.1, disabled=not editable_inputs
        )
        shipping_days = st.number_input(
            "Shipping days", value=int(state.shipping_days), step=1, disabled=not editable_inputs
        )
        supplier_rating = st.number_input(
            "Supplier rating", value=float(state.supplier_rating), step=0.1, disabled=not editable_inputs
        )
        submitted = st.form_submit_button("Save inputs", disabled=not editable_inputs)

    if submitted and editable_inputs:
        updated_state = state.model_copy(deep=True)
        updated_state.product_name = product_name
        updated_state.supplier_cost = supplier_cost
        updated_state.shipping_days = int(shipping_days)
        updated_state.supplier_rating = supplier_rating

        if state.stage == "HUMAN_REVIEW":
            updated_state = reset_pipeline(updated_state, "Inputs changed during HUMAN_REVIEW; pipeline reset.")
        else:
            log_event(updated_state, "Product inputs updated.")
        persist_and_rerun(updated_state)
    elif submitted and not editable_inputs:
        st.info("Inputs are locked until review is complete.")

    st.divider()
    cols = st.columns(3)
    with cols[0]:
        display_json_block("Research output", state.research)
    with cols[1]:
        display_json_block("Pricing output", state.pricing)
    with cols[2]:
        display_json_block("Content output", state.content)

    st.divider()
    st.subheader("Audit log (latest 20)")
    if state.audit_log:
        for entry in reversed(state.audit_log[-20:]):
            ts = entry.get("timestamp", "")
            level = entry.get("level", "info").upper()
            stage = entry.get("stage", "")
            message = entry.get("message", "")
            st.write(f"{ts} [{level}] ({stage}) {message}")
    else:
        st.info("No audit entries yet.")

    if state.stage == "HUMAN_REVIEW":
        st.divider()
        st.subheader("Human review")
        approve_col, reject_col = st.columns(2)
        with approve_col:
            if st.button("Approve", type="primary"):
                updated_state = state.model_copy(deep=True)
                updated_state.stage = "APPROVED"
                log_event(updated_state, "Pipeline approved by human.", level="success")
                persist_and_rerun(updated_state)
        with reject_col:
            if st.button("Reject", type="secondary"):
                updated_state = state.model_copy(deep=True)
                updated_state.stage = "REJECTED"
                log_event(updated_state, "Pipeline rejected by human.", level="warning")
                persist_and_rerun(updated_state)


if __name__ == "__main__":
    main()
