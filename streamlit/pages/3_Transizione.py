import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_sessione, aggiorna_sessione, get_fenomeni, crea_scenari
from lib.auth import check_auth

st.set_page_config(page_title="Transizione · Foresight Facilitator", page_icon="🔀", layout="wide")
check_auth()

if "sessione_id" not in st.session_state:
    st.warning("Nessuna sessione selezionata.")
    st.page_link("app.py", label="← Torna alla home")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione(sid)

st.markdown(f"### 🔀 Transizione — Sessione #{sid}")
st.caption(f"Orizzonte: **{sessione['frame_temporale']}**")
with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

# ── Top fenomeni ──────────────────────────────────────────
fenomeni = get_fenomeni(sid)
st.subheader("🏆 Fenomeni prioritizzati")
st.caption("Usa questi risultati per identificare i 2 driver principali")

cols = st.columns(min(len(fenomeni), 4))
for i, f in enumerate(fenomeni[:8]):
    with cols[i % 4]:
        with st.container(border=True):
            badge = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}°"
            st.markdown(f"{badge} **{f['testo']}**")
            if f.get("descrizione"):
                st.caption(f["descrizione"])

st.divider()

# ── Selezione Driver ──────────────────────────────────────
st.subheader("🎯 Definisci i 2 Driver")
st.caption("I driver sono le due forze chiave più rilevanti e incerte. Definiranno gli assi della matrice 2×2.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Driver 1 (Asse X)")
    d1_nome = st.text_input(
        "Nome del driver",
        value=sessione.get("driver1_nome") or "",
        placeholder="Es. Adozione tecnologica",
        key="d1_nome"
    )
    col_d1a, col_d1b = st.columns(2)
    with col_d1a:
        d1_pos = st.text_input(
            "Polo +",
            value=sessione.get("driver1_pos") or "",
            placeholder="Es. Alta adozione",
            key="d1_pos"
        )
    with col_d1b:
        d1_neg = st.text_input(
            "Polo −",
            value=sessione.get("driver1_neg") or "",
            placeholder="Es. Bassa adozione",
            key="d1_neg"
        )

with col2:
    st.markdown("#### Driver 2 (Asse Y)")
    d2_nome = st.text_input(
        "Nome del driver",
        value=sessione.get("driver2_nome") or "",
        placeholder="Es. Centralizzazione del potere",
        key="d2_nome"
    )
    col_d2a, col_d2b = st.columns(2)
    with col_d2a:
        d2_pos = st.text_input(
            "Polo +",
            value=sessione.get("driver2_pos") or "",
            placeholder="Es. Alta centralizzazione",
            key="d2_pos"
        )
    with col_d2b:
        d2_neg = st.text_input(
            "Polo −",
            value=sessione.get("driver2_neg") or "",
            placeholder="Es. Bassa centralizzazione",
            key="d2_neg"
        )

if st.button("💾 Salva Driver", use_container_width=True):
    if not d1_nome.strip() or not d2_nome.strip():
        st.error("Inserisci il nome di entrambi i driver.")
    else:
        aggiorna_sessione(
            sid,
            driver1_nome=d1_nome.strip(),
            driver1_pos=d1_pos.strip(),
            driver1_neg=d1_neg.strip(),
            driver2_nome=d2_nome.strip(),
            driver2_pos=d2_pos.strip(),
            driver2_neg=d2_neg.strip(),
        )
        st.success("Driver salvati!")
        st.rerun()

st.divider()

# ── Anteprima matrice 2×2 ─────────────────────────────────
sessione = get_sessione(sid)  # ricarica

if sessione.get("driver1_nome") and sessione.get("driver2_nome"):
    st.subheader("🗺️ Anteprima Matrice 2×2")

    d1 = sessione["driver1_nome"]
    d1p = sessione.get("driver1_pos") or f"{d1} alto"
    d1n = sessione.get("driver1_neg") or f"{d1} basso"
    d2 = sessione["driver2_nome"]
    d2p = sessione.get("driver2_pos") or f"{d2} alto"
    d2n = sessione.get("driver2_neg") or f"{d2} basso"

    st.markdown(f"<center><small>↑ {d2p}</small></center>", unsafe_allow_html=True)

    q_col1, q_col2 = st.columns(2)
    with q_col1:
        with st.container(border=True):
            st.markdown(f"**Scenario 3** `−+`")
            st.caption(f"{d1n} × {d2p}")
        with st.container(border=True):
            st.markdown(f"**Scenario 4** `−−`")
            st.caption(f"{d1n} × {d2n}")
    with q_col2:
        with st.container(border=True):
            st.markdown(f"**Scenario 1** `++`")
            st.caption(f"{d1p} × {d2p}")
        with st.container(border=True):
            st.markdown(f"**Scenario 2** `+−`")
            st.caption(f"{d1p} × {d2n}")

    st.markdown(f"<center><small>↓ {d2n}</small></center>", unsafe_allow_html=True)
    st.caption(f"← {d1n} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {d1p} →", unsafe_allow_html=True)

    st.divider()
    if st.button("🗺️ Avvia Scenario Planning", type="primary", use_container_width=True):
        crea_scenari(sid)
        aggiorna_sessione(sid, stato="scenario_planning")
        st.switch_page("pages/4_Scenario_Planning.py")
else:
    st.info("Definisci e salva entrambi i driver per vedere l'anteprima della matrice.")
