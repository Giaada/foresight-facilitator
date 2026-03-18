import streamlit as st
import os


def get_password():
    try:
        return st.secrets["FACILITATOR_PASSWORD"]
    except Exception:
        return os.environ.get("FACILITATOR_PASSWORD", "foresight2025")


def check_facilitatore():
    """Controlla che il ruolo sia 'facilitatore'. Se no, mostra form login e blocca."""
    if st.session_state.get("ruolo") == "facilitatore":
        return

    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🧭 Foresight Facilitator")
        st.markdown("**Area riservata al facilitatore**")
        st.divider()

        with st.form("login_form_fac"):
            password = st.text_input("Password", type="password", placeholder="Inserisci la password")
            submitted = st.form_submit_button("Accedi", use_container_width=True, type="primary")

        if submitted:
            if password == get_password():
                st.session_state["ruolo"] = "facilitatore"
                st.rerun()
            else:
                st.error("Password non corretta.")

    st.stop()


# Alias per compatibilità con eventuali import residui
def check_auth():
    check_facilitatore()
