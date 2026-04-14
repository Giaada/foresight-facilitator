import streamlit as st
from .database import aggiorna_fenomeno, elimina_fenomeno


def fenomeno_row(f, key_prefix=""):
    prefix = f"{key_prefix}_" if key_prefix else ""
    fid = f["id"]
    col_f, col_edit, col_del = st.columns([5, 1, 1])
    with col_f:
        st.markdown(f"**{f['testo']}**")
        if f.get("descrizione"):
            st.caption(f["descrizione"])
    with col_edit:
        with st.popover("✏️"):
            edit_testo = st.text_input("Testo", value=f["testo"], key=f"{prefix}et_{fid}")
            edit_desc = st.text_area("Descrizione", value=f.get("descrizione", ""), key=f"{prefix}ed_{fid}")
            if st.button("Salva", key=f"{prefix}esave_{fid}", type="primary"):
                aggiorna_fenomeno(fid, edit_testo.strip(), edit_desc.strip())
                st.rerun(scope="app")
    with col_del:
        if st.button("🗑️", key=f"{prefix}del_{fid}", help="Elimina"):
            elimina_fenomeno(fid)
            st.rerun(scope="app")
