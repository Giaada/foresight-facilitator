import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import (
    get_sessione_by_id, aggiorna_sessione, get_fenomeni,
    get_partecipanti, aggiorna_partecipante, crea_scenari, get_voti_aggregati
)
from lib.quadrant_ui import draw_quadrant_matrix

check_facilitatore()

if not st.session_state.get("sessione_id"):
    st.warning("Nessuna sessione attiva. Vai su Setup per aprire o creare una sessione.")
    st.stop()

sid = st.session_state["sessione_id"]
sessione = get_sessione_by_id(sid)

if not sessione:
    st.error("Sessione non trovata.")
    st.stop()

st.markdown(f"### 🔀 Transizione — Sessione #{sid}")
st.caption(f"Orizzonte: **{sessione['frame_temporale']}**")

with st.expander("📌 Domanda di ricerca"):
    st.info(sessione["domanda_ricerca"])

st.divider()

# ── Top fenomeni per priorità aggregata ───────────────────
st.subheader("🏆 Fenomeni per priorità aggregata")
st.caption("Usa questi risultati per identificare i 2 driver principali")

voti = get_voti_aggregati(sid)
fenomeni = get_fenomeni(sid)
fenom_map = {f["id"]: f for f in fenomeni}

if voti:
    cols = st.columns(min(len(voti), 4))
    for i, v in enumerate(voti[:8]):
        f = fenom_map.get(v["fenomeno_id"])
        testo = f["testo"] if f else f"Fenomeno #{v['fenomeno_id']}"
        with cols[i % 4]:
            with st.container(border=True):
                badge = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}°"
                st.markdown(f"{badge} **{testo}**")
                st.caption(f"avg pos: {v['media_posizione']:.1f}")
else:
    # Fallback: mostra fenomeni per priorità manuale
    for i, f in enumerate(fenomeni[:8]):
        with st.container(border=True):
            badge = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}°"
            st.markdown(f"{badge} **{f['testo']}**")
            if f.get("descrizione"):
                st.caption(f["descrizione"])

st.divider()

# ── Definisci Driver ──────────────────────────────────────
st.subheader("🎯 Definisci i 2 Driver")
st.caption("I driver sono le due forze chiave più rilevanti e incerte. Definiranno gli assi della matrice 2×2.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Driver 1 (Asse X)")
    d1_nome = st.text_input(
        "Nome del driver",
        value=sessione.get("driver1_nome") or "",
        placeholder="Es. Adozione tecnologica",
        key="d1_nome",
    )
    col_d1a, col_d1b = st.columns(2)
    with col_d1a:
        d1_pos = st.text_input(
            "Polo +",
            value=sessione.get("driver1_pos") or "",
            placeholder="Es. Alta adozione",
            key="d1_pos",
        )
    with col_d1b:
        d1_neg = st.text_input(
            "Polo −",
            value=sessione.get("driver1_neg") or "",
            placeholder="Es. Bassa adozione",
            key="d1_neg",
        )

with col2:
    st.markdown("#### Driver 2 (Asse Y)")
    d2_nome = st.text_input(
        "Nome del driver",
        value=sessione.get("driver2_nome") or "",
        placeholder="Es. Centralizzazione del potere",
        key="d2_nome",
    )
    col_d2a, col_d2b = st.columns(2)
    with col_d2a:
        d2_pos = st.text_input(
            "Polo +",
            value=sessione.get("driver2_pos") or "",
            placeholder="Es. Alta centralizzazione",
            key="d2_pos",
        )
    with col_d2b:
        d2_neg = st.text_input(
            "Polo −",
            value=sessione.get("driver2_neg") or "",
            placeholder="Es. Bassa centralizzazione",
            key="d2_neg",
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
sessione = get_sessione_by_id(sid)  # ricarica dopo eventuale salvataggio

if sessione.get("driver1_nome") and sessione.get("driver2_nome"):
    st.subheader("🗺️ Anteprima Matrice 2×2")

    d1 = sessione["driver1_nome"]
    d1p = sessione.get("driver1_pos") or f"{d1} alto"
    d1n = sessione.get("driver1_neg") or f"{d1} basso"
    d2 = sessione["driver2_nome"]
    d2p = sessione.get("driver2_pos") or f"{d2} alto"
    d2n = sessione.get("driver2_neg") or f"{d2} basso"

    # Render grafica
    st.markdown(draw_quadrant_matrix(None, d1p, d1n, d2p, d2n), unsafe_allow_html=True)

    st.divider()

    # ── Assegnazione gruppi ───────────────────────────────
    st.subheader("👥 Assegnazione gruppi ai partecipanti")
    st.caption("Assegna ogni partecipante a uno dei 4 scenari")

    GRUPPI_LABEL = {
        1: "Gruppo 1 (++)",
        2: "Gruppo 2 (+-)",
        3: "Gruppo 3 (-+)",
        4: "Gruppo 4 (--)",
    }
    partecipanti = get_partecipanti(sid)

    if not partecipanti:
        st.info("Nessun partecipante ancora connesso.")
    else:
        gruppi_updates = {}
        cols_par = st.columns(min(len(partecipanti), 3))
        for i, p in enumerate(partecipanti):
            with cols_par[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{p['nome']}**")
                    opzioni = [0] + list(range(1, 5))
                    label_opzioni = ["Non assegnato"] + [GRUPPI_LABEL[g] for g in range(1, 5)]
                    valore_attuale = p.get("gruppo_numero") or 0
                    sel = st.selectbox(
                        "Gruppo",
                        options=opzioni,
                        index=opzioni.index(valore_attuale) if valore_attuale in opzioni else 0,
                        format_func=lambda x: "Non assegnato" if x == 0 else GRUPPI_LABEL[x],
                        key=f"gruppo_{p['id']}",
                        label_visibility="collapsed",
                    )
                    gruppi_updates[p["id"]] = sel if sel != 0 else None

        if st.button("💾 Salva assegnazione gruppi", use_container_width=True):
            for pid, gnum in gruppi_updates.items():
                aggiorna_partecipante(pid, gruppo_numero=gnum)
            st.success("Gruppi salvati!")
            st.rerun()

    st.divider()

    if st.button("▶️ Avvia Scenario Planning", type="primary", use_container_width=True):
        # Salva eventuali gruppi prima di avanzare
        crea_scenari(sid)
        aggiorna_sessione(sid, stato="scenario_planning")
        st.success("Scenario Planning avviato!")
        st.switch_page("pages/fac_scenario.py")

else:
    st.info("Definisci e salva entrambi i driver per vedere l'anteprima della matrice e assegnare i gruppi.")
