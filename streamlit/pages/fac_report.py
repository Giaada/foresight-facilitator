import streamlit as st
import sys
from pathlib import Path
import markdown
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.auth import check_facilitatore
from lib.database import get_sessione_by_id, get_scenari, get_fenomeni, get_voti_aggregati
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

scenari = get_scenari(sid)
fenomeni = get_fenomeni(sid)
voti = get_voti_aggregati(sid)
fenom_map = {f["id"]: f for f in fenomeni}

# ── Header ─────────────────────────────────────────────────
st.markdown(f"# 📄 Report Finale — Sessione #{sid}")
st.caption(f"Generato il {sessione['created_at'][:10]}")
st.divider()

# ── Contesto ───────────────────────────────────────────────
st.subheader("📌 Contesto della sessione")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Domanda di ricerca**")
    st.info(sessione["domanda_ricerca"])
with col2:
    st.markdown("**Orizzonte temporale**")
    st.success(f"⏱️ {sessione['frame_temporale']}")

if sessione.get("driver1_nome") and sessione.get("driver2_nome"):
    st.markdown("**Driver principali**")
    dc1, dc2 = st.columns(2)
    with dc1:
        with st.container(border=True):
            st.markdown(f"**Driver 1 — {sessione['driver1_nome']}**")
            st.caption(f"+ {sessione.get('driver1_pos', '—')} / − {sessione.get('driver1_neg', '—')}")
    with dc2:
        with st.container(border=True):
            st.markdown(f"**Driver 2 — {sessione['driver2_nome']}**")
            st.caption(f"+ {sessione.get('driver2_pos', '—')} / − {sessione.get('driver2_neg', '—')}")

st.divider()

# ── Top fenomeni ───────────────────────────────────────────
st.subheader("🔭 Fenomeni prioritizzati")

# Usa ranking aggregato dai voti se disponibile, altrimenti ordine manuale
if voti:
    st.caption("Ordinati per posizione media dei voti dei partecipanti")
    for i, v in enumerate(voti[:10]):
        f = fenom_map.get(v["fenomeno_id"])
        testo = f["testo"] if f else f"Fenomeno #{v['fenomeno_id']}"
        col_n, col_t, col_info = st.columns([1, 8, 2])
        with col_n:
            color = "#4F46E5" if i < 3 else "#6B7280"
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>",
                unsafe_allow_html=True,
            )
        with col_t:
            peso = "**" if i < 3 else ""
            st.markdown(f"{peso}{testo}{peso}")
        with col_info:
            st.caption(f"avg: {v['media_posizione']:.1f}")
else:
    for i, f in enumerate(fenomeni[:10]):
        col_n, col_t = st.columns([1, 9])
        with col_n:
            color = "#4F46E5" if i < 3 else "#6B7280"
            st.markdown(
                f"<span style='color:{color};font-weight:bold;font-size:1.1em'>{i+1}</span>",
                unsafe_allow_html=True,
            )
        with col_t:
            peso = "**" if i < 3 else ""
            st.markdown(f"{peso}{f['testo']}{peso}")

st.divider()

# ── Matrice 2×2 ────────────────────────────────────────────
st.subheader("🗺️ Matrice degli Scenari")

if scenari and sessione.get("driver1_nome"):
    d1 = sessione["driver1_nome"]
    d2 = sessione["driver2_nome"]
    d1p = sessione.get("driver1_pos") or f"{d1} +"
    d1n = sessione.get("driver1_neg") or f"{d1} −"
    d2p = sessione.get("driver2_pos") or f"{d2} +"
    d2n = sessione.get("driver2_neg") or f"{d2} −"

    sc_map = {s["quadrante"]: s for s in scenari}

    st.markdown(draw_quadrant_matrix(None, d1p, d1n, d2p, d2n), unsafe_allow_html=True)

st.divider()

# ── Scenari nel dettaglio ──────────────────────────────────
st.subheader("📖 Scenari nel dettaglio")

for sc in scenari:
    titolo = sc.get("titolo") or f"Scenario {sc['numero']}"
    with st.expander(f"**{titolo}** — Quadrante `{sc['quadrante']}`", expanded=True):
        if sc.get("narrativa"):
            st.markdown("**Descrizione**")
            st.markdown(sc["narrativa"])

        if sc.get("key_points_data"):
            st.markdown("**Key Points esplorati**")
            for kp, ris in sc["key_points_data"].items():
                st.markdown(f"- **{kp}:** {ris}")

        col_m, col_o = st.columns(2)
        with col_m:
            if sc.get("minacce"):
                st.markdown("**⚠️ Minacce**")
                for m in sc["minacce"]:
                    st.markdown(f"- {m}")
        with col_o:
            if sc.get("opportunita"):
                st.markdown("**✨ Opportunità**")
                for o in sc["opportunita"]:
                    st.markdown(f"- {o}")

st.divider()

# ── Export ─────────────────────────────────────────────────
st.subheader("💾 Esporta")


from lib.pdf_export import st_scarica_pdf_report_finale
from lib.database import get_partecipanti as _get_partecipanti_report
_partecipanti_report = _get_partecipanti_report(sid)

md = st_scarica_pdf_report_finale(sessione, scenari, fenomeni, voti, partecipanti=_partecipanti_report)

st.download_button(
    label="Scarica File Sorgente (Markdown grezzo)",
    data=md.encode("utf-8"),
    file_name=f"foresight_report_sessione_{sid}.md",
    mime="text/markdown",
    use_container_width=True,
)

with st.expander("Anteprima Markdown"):
    st.code(md, language="markdown")
