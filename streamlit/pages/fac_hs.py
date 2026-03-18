import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import (
    get_sessione_by_id, aggiorna_sessione, get_fenomeni,
    get_partecipanti, get_voti_aggregati, aggiungi_fenomeno, elimina_fenomeno
)

check_facilitatore()

if not st.session_state.get("sessione_id"):
    st.warning("Nessuna sessione attiva. Vai su Setup per aprire o creare una sessione.")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione_by_id(sid)

if not sessione:
    st.error("Sessione non trovata.")
    st.stop()

st.markdown(f"### 🔭 Horizon Scanning — Sessione #{sid}")
st.caption(f"Orizzonte: **{sessione['frame_temporale']}** · Codice: `{sessione.get('codice', '—')}`")

with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

col_left, col_right = st.columns(2)

# ── COLONNA SINISTRA: partecipanti e progresso ────────────
with col_left:
    st.subheader("👥 Partecipanti")

    @st.fragment(run_every=10)
    def _mostra_partecipanti():
        partecipanti = get_partecipanti(sid)
        n_votato = sum(1 for p in partecipanti if p["votato"])
        n_totale = len(partecipanti)

        st.markdown(f"**{n_votato}/{n_totale} hanno votato**")
        if n_totale > 0:
            st.progress(n_votato / n_totale)
        else:
            st.progress(0.0)

        if not partecipanti:
            st.info("Nessun partecipante ancora connesso. Condividi il codice sessione.")
        else:
            # Tabella partecipanti
            for p in partecipanti:
                stato_voto = "✅" if p["votato"] else "⏳"
                gruppo_str = f"Gruppo {p['gruppo_numero']}" if p.get("gruppo_numero") else "—"
                col_nome, col_voto, col_gr = st.columns([3, 1, 2])
                with col_nome:
                    st.markdown(f"**{p['nome']}**")
                with col_voto:
                    st.markdown(stato_voto)
                with col_gr:
                    st.caption(gruppo_str)

    _mostra_partecipanti()

# ── COLONNA DESTRA: ranking aggregato ────────────────────
with col_right:
    st.subheader("📊 Ranking aggregato")

    @st.fragment(run_every=10)
    def _mostra_ranking():
        voti = get_voti_aggregati(sid)
        fenomeni = get_fenomeni(sid)
        fenom_map = {f["id"]: f for f in fenomeni}

        if not voti:
            st.info("Nessun voto ancora ricevuto. I risultati appariranno man mano che i partecipanti votano.")
        else:
            st.caption("Ordinato per posizione media (più bassa = più prioritario)")
            for i, v in enumerate(voti):
                f = fenom_map.get(v["fenomeno_id"])
                testo = f["testo"] if f else f"Fenomeno #{v['fenomeno_id']}"
                col_pos, col_bar, col_testo, col_info = st.columns([1, 2, 5, 2])
                with col_pos:
                    color = "#4F46E5" if i < 3 else "#9CA3AF"
                    st.markdown(
                        f"<span style='color:{color};font-weight:bold'>{i+1}</span>",
                        unsafe_allow_html=True,
                    )
                with col_bar:
                    max_pos = len(fenomeni) if fenomeni else 1
                    bar_val = max(0.05, 1.0 - (v["media_posizione"] - 1) / max(max_pos - 1, 1))
                    st.progress(bar_val)
                with col_testo:
                    peso = "**" if i < 3 else ""
                    st.markdown(f"{peso}{testo}{peso}")
                with col_info:
                    st.caption(f"avg: {v['media_posizione']:.1f} · n={v['conteggio']}")

        st.divider()
        st.subheader("📋 Fenomeni in lista")
        fenomeni_tutti = get_fenomeni(sid)
        for f in fenomeni_tutti:
            col_t, col_d = st.columns([5, 1])
            with col_t:
                st.markdown(f"**{f['testo']}**")
                if f.get("descrizione"):
                    st.caption(f["descrizione"])
            with col_d:
                if st.button("🗑️", key=f"rm_hs_{f['id']}", help="Elimina"):
                    elimina_fenomeno(f["id"])
                    st.rerun()

    _mostra_ranking()

st.divider()

# ── Aggiungi fenomeno ─────────────────────────────────────
st.subheader("➕ Aggiungi fenomeno")
_fen_submitted = False
with st.form("aggiungi_fenomeno_hs", clear_on_submit=True):
    col_t, col_d, col_btn = st.columns([4, 4, 1])
    with col_t:
        nuovo_testo = st.text_input("Fenomeno / trend", placeholder="Scrivi il fenomeno...", label_visibility="collapsed")
    with col_d:
        nuova_descr = st.text_input("Descrizione (opzionale)", placeholder="Breve spiegazione...", label_visibility="collapsed")
    with col_btn:
        _fen_submitted = st.form_submit_button("Aggiungi", use_container_width=True, type="primary")

if _fen_submitted:
    if nuovo_testo.strip():
        aggiungi_fenomeno(sid, nuovo_testo.strip(), nuova_descr.strip())
    st.rerun()

st.divider()

# ── Avanza alla Transizione ───────────────────────────────
if st.button("🔀 Vai alla Transizione", type="primary", use_container_width=True):
    aggiorna_sessione(sid, stato="transizione")
    st.switch_page("pages/fac_transizione.py")
