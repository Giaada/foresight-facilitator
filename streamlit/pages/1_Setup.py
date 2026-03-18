import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_sessione, aggiorna_sessione, get_fenomeni, aggiungi_fenomeno, elimina_fenomeno
from lib.auth import check_auth

st.set_page_config(page_title="Setup · Foresight Facilitator", page_icon="⚙️", layout="wide")
check_auth()

if "sessione_id" not in st.session_state:
    st.warning("Nessuna sessione selezionata.")
    st.page_link("app.py", label="← Torna alla home")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione(sid)

# ── Header ────────────────────────────────────────────────
st.markdown(f"### ⚙️ Setup — Sessione #{sid}")
st.caption(f"🔭 {sessione['frame_temporale']} · Stato: `{sessione['stato']}`")

with st.expander("📌 Domanda di ricerca", expanded=True):
    st.info(sessione["domanda_ricerca"])

st.divider()

col1, col2 = st.columns(2)

# ── Key Points ───────────────────────────────────────────
with col1:
    st.subheader("🎯 Key Points")
    st.caption("Dimensioni che ogni scenario dovrà esplorare nello Scenario Planning")

    kp_attuale = "\n".join(sessione["key_points"])
    kp_nuovo = st.text_area(
        "Un key point per riga",
        value=kp_attuale,
        height=150,
        label_visibility="collapsed",
    )
    if st.button("Salva Key Points", use_container_width=True):
        nuovi = [k.strip() for k in kp_nuovo.strip().splitlines() if k.strip()]
        import json
        aggiorna_sessione(sid, key_points=json.dumps(nuovi))
        st.success("Key points aggiornati!")
        st.rerun()

    if sessione["key_points"]:
        st.markdown("**Key points correnti:**")
        for kp in sessione["key_points"]:
            st.markdown(f"- {kp}")

# ── Fenomeni ─────────────────────────────────────────────
with col2:
    st.subheader("📋 Fenomeni / Trend")
    st.caption("Lista dei fenomeni che i partecipanti valuteranno nella fase di Horizon Scanning")

    fenomeni = get_fenomeni(sid)
    st.markdown(f"**{len(fenomeni)} fenomeni inseriti:**")

    for f in fenomeni:
        col_f, col_del = st.columns([5, 1])
        with col_f:
            st.markdown(f"**{f['testo']}**")
            if f.get("descrizione"):
                st.caption(f['descrizione'])
        with col_del:
            if st.button("🗑️", key=f"del_{f['id']}", help="Elimina"):
                elimina_fenomeno(f["id"])
                st.rerun()

    st.divider()
    with st.form("aggiungi_fenomeno", clear_on_submit=True):
        st.markdown("**Aggiungi fenomeno**")
        nuovo_testo = st.text_input("Testo del fenomeno", placeholder="Es. Intelligenza Artificiale generativa")
        nuova_descr = st.text_input("Descrizione (opzionale)", placeholder="Breve spiegazione...")
        if st.form_submit_button("Aggiungi", use_container_width=True):
            if nuovo_testo.strip():
                aggiungi_fenomeno(sid, nuovo_testo.strip(), nuova_descr.strip())
                st.rerun()

st.divider()

# ── Avvia ─────────────────────────────────────────────────
st.subheader("🚀 Avvia la sessione")

fenomeni_count = len(get_fenomeni(sid))
kp_count = len(sessione["key_points"])

col_check1, col_check2, col_check3 = st.columns(3)
with col_check1:
    stato_f = "✅" if fenomeni_count >= 2 else "⚠️"
    st.metric(f"{stato_f} Fenomeni", fenomeni_count, help="Minimo 2 consigliati")
with col_check2:
    stato_kp = "✅" if kp_count >= 1 else "⚠️"
    st.metric(f"{stato_kp} Key Points", kp_count)
with col_check3:
    st.metric("📌 Orizzonte", sessione["frame_temporale"])

if st.button("▶️ Avvia Horizon Scanning", type="primary", use_container_width=True, disabled=fenomeni_count < 1):
    aggiorna_sessione(sid, stato="horizon_scanning")
    st.success("Sessione avviata!")
    st.switch_page("pages/2_Horizon_Scanning.py")
