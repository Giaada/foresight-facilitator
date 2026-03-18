import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import (
    get_sessione, aggiorna_sessione, get_fenomeni,
    aggiungi_fenomeno, elimina_fenomeno, aggiorna_priorita_fenomeni
)

try:
    from streamlit_sortables import sort_items
    SORTABLE = True
except ImportError:
    SORTABLE = False

st.set_page_config(page_title="Horizon Scanning · Foresight Facilitator", page_icon="🔭", layout="wide")

if "sessione_id" not in st.session_state:
    st.warning("Nessuna sessione selezionata.")
    st.page_link("app.py", label="← Torna alla home")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione(sid)

# ── Header ────────────────────────────────────────────────
st.markdown(f"### 🔭 Horizon Scanning — Sessione #{sid}")
st.caption(f"Orizzonte: **{sessione['frame_temporale']}**")

with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

fenomeni = get_fenomeni(sid)
col1, col2 = st.columns([3, 2])

# ── Prioritizzazione ─────────────────────────────────────
with col1:
    st.subheader("📊 Prioritizzazione fenomeni")
    st.caption("Ordina i fenomeni dal più al meno rilevante rispetto alla domanda di ricerca")

    if not fenomeni:
        st.info("Nessun fenomeno inserito. Torna al Setup per aggiungerli.")
    elif SORTABLE:
        items = [f["testo"] for f in fenomeni]
        sorted_items = sort_items(items, direction="vertical", key="sort_fenomeni")
        if sorted_items != items:
            id_map = {f["testo"]: f["id"] for f in fenomeni}
            nuovo_ordine = [id_map[t] for t in sorted_items if t in id_map]
            aggiorna_priorita_fenomeni(sid, nuovo_ordine)
            st.rerun()

        st.markdown("**Ordine corrente:**")
        for i, f in enumerate(fenomeni):
            with st.container(border=True):
                col_n, col_t = st.columns([1, 8])
                with col_n:
                    st.markdown(f"**{i+1}**")
                with col_t:
                    st.markdown(f"**{f['testo']}**")
                    if f.get("descrizione"):
                        st.caption(f["descrizione"])
    else:
        # Fallback senza drag: numeri di priorità
        st.info("💡 Installa `streamlit-sortables` per il drag & drop. Usa i numeri per prioritizzare.")
        nuovi_ordini = {}
        for f in fenomeni:
            nuovi_ordini[f["id"]] = st.number_input(
                f["testo"],
                min_value=1,
                max_value=len(fenomeni),
                value=f["priorita"] if f["priorita"] < 999 else (fenomeni.index(f) + 1),
                key=f"prio_{f['id']}"
            )
        if st.button("Salva ordine", use_container_width=True):
            ordinato = sorted(nuovi_ordini.items(), key=lambda x: x[1])
            aggiorna_priorita_fenomeni(sid, [fid for fid, _ in ordinato])
            st.success("Ordine salvato!")
            st.rerun()

# ── Gestione fenomeni ────────────────────────────────────
with col2:
    st.subheader("➕ Aggiungi fenomeno")
    with st.form("nuovo_fenomeno_hs", clear_on_submit=True):
        testo = st.text_input("Fenomeno / trend", placeholder="Scrivi il fenomeno...")
        descr = st.text_input("Descrizione (opzionale)")
        if st.form_submit_button("Aggiungi", use_container_width=True):
            if testo.strip():
                aggiungi_fenomeno(sid, testo.strip(), descr.strip())
                st.rerun()

    st.divider()
    st.subheader("🗑️ Rimuovi fenomeni")
    for f in fenomeni:
        col_t, col_d = st.columns([4, 1])
        with col_t:
            st.markdown(f"*{f['testo']}*")
        with col_d:
            if st.button("✕", key=f"rm_{f['id']}"):
                elimina_fenomeno(f["id"])
                st.rerun()

st.divider()

# ── Riepilogo e avanzamento ───────────────────────────────
st.subheader("📈 Riepilogo prioritizzazione")

fenomeni_aggiornati = get_fenomeni(sid)
if fenomeni_aggiornati:
    for i, f in enumerate(fenomeni_aggiornati):
        bar_width = max(10, 100 - i * (80 // max(len(fenomeni_aggiornati), 1)))
        col_pos, col_bar, col_nome = st.columns([1, 2, 6])
        with col_pos:
            color = "#4F46E5" if i < 3 else "#9CA3AF"
            st.markdown(f"<span style='color:{color};font-weight:bold'>{i+1}</span>", unsafe_allow_html=True)
        with col_bar:
            st.progress(bar_width / 100)
        with col_nome:
            st.markdown(f"{'**' if i < 3 else ''}{f['testo']}{'**' if i < 3 else ''}")

st.divider()
if st.button("🔀 Vai alla Transizione", type="primary", use_container_width=True):
    aggiorna_sessione(sid, stato="transizione")
    st.switch_page("pages/3_Transizione.py")
