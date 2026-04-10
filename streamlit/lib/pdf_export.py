import markdown
import streamlit.components.v1 as components

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def st_scarica_pdf_scenario_individuale(scenario_indiv, sessione, nome_partecipante):
    # Costruisce HTML direttamente (evita problemi di parsing con markdown.markdown)
    sezioni = []

    sezioni.append(f"<h1>Scenario Individuale — {_esc(nome_partecipante)}</h1>")
    sezioni.append(
        f"<p><strong>Sessione:</strong> {_esc(sessione['domanda_ricerca'])}<br>"
        f"<strong>Orizzonte temporale:</strong> {_esc(sessione['frame_temporale'])}<br>"
        f"<strong>Quadrante assegnato:</strong> <code>{_esc(scenario_indiv['quadrante'])}</code></p>"
    )

    if scenario_indiv.get("titolo"):
        sezioni.append(
            f"<div class='scenario-title-box'>"
            f"<span class='scenario-label'>Scenario {scenario_indiv['numero']}</span>"
            f"<h2 class='scenario-name'>{_esc(scenario_indiv['titolo'])}</h2>"
            f"</div>"
        )

    if scenario_indiv.get("narrativa"):
        sezioni.append(f"<h3>📖 Narrativa</h3><p>{_esc(scenario_indiv['narrativa']).replace(chr(10), '<br>')}</p>")

    if scenario_indiv.get("key_points_data"):
        kp_items = "".join(
            f"<li><strong>{_esc(kp)}:</strong> {_esc(ris)}</li>"
            for kp, ris in scenario_indiv["key_points_data"].items()
        )
        sezioni.append(f"<h3>🎯 Key Points Esplorati</h3><ul>{kp_items}</ul>")

    if scenario_indiv.get("minacce"):
        items = "".join(f"<li>{_esc(m)}</li>" for m in scenario_indiv["minacce"])
        sezioni.append(f"<div class='box minacce'><h4>⚠️ Minacce</h4><ul>{items}</ul></div>")

    if scenario_indiv.get("opportunita"):
        items = "".join(f"<li>{_esc(o)}</li>" for o in scenario_indiv["opportunita"])
        sezioni.append(f"<div class='box opportunita'><h4>✨ Opportunità</h4><ul>{items}</ul></div>")

    html_content = "\n".join(sezioni)
    
    unique_id = f"pdf-sc-{scenario_indiv['id']}"

    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
      * {{ box-sizing: border-box; word-wrap: break-word; overflow-wrap: break-word; }}
      body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; color: #333; margin: 0; }}
      #{unique_id} {{ padding: 20px 30px; max-width: 700px; margin: 0 auto; }}
      #{unique_id} h1 {{ color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 10px; margin-bottom: 20px; font-size: 22px; }}
      #{unique_id} h3 {{ color: #4338CA; margin-top: 20px; }}
      #{unique_id} p, #{unique_id} li {{ line-height: 1.6; font-size: 13px; position: relative; z-index: 1; }}
      .box {{ padding: 15px; margin-top: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 5px solid; }}
      .box h4 {{ margin-top: 0 !important; margin-bottom: 10px; font-size: 15px; padding-bottom: 5px; }}
      .box ul {{ margin-bottom: 0; padding-left: 20px; }}
      .box.minacce {{ background-color: #FEF2F2; border-left-color: #EF4444; }}
      .box.minacce h4 {{ color: #991B1B !important; }}
      .box.opportunita {{ background-color: #ECFDF5; border-left-color: #10B981; }}
      .box.opportunita h4 {{ color: #065F46 !important; }}
      .box.comune {{ background-color: #EFF6FF; border-left-color: #3B82F6; }}
      .box.comune h4 {{ color: #1E3A8A !important; }}
      .box.divergenze {{ background-color: #FEFCE8; border-left-color: #EAB308; }}
      .box.divergenze h4 {{ color: #854D0E !important; }}
      .scenario-title-box {{ background-color: #E0F2FE; border: 2px solid #0284C7; border-radius: 8px; padding: 15px 20px; margin-top: 20px; margin-bottom: 25px; text-align: center; page-break-after: avoid; }}
      .scenario-label {{ display: block; font-size: 13px; font-weight: 700; color: #0369A1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
      .scenario-name {{ color: #0C4A6E !important; margin: 0 !important; padding: 0 !important; border: none !important; font-size: 22px; }}
      .scenario-quadrant {{ display: inline-block; margin-top: 10px; background-color: #BAE6FD; color: #075985; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
      .toc {{ list-style: none; padding-left: 0; margin-bottom: 30px; page-break-after: always; }}
      .toc li {{ margin-bottom: 10px; padding: 12px; background-color: #F8FAFC; border-left: 4px solid #94A3B8; border-radius: 4px; }}
      .toc a {{ text-decoration: none; color: #334155; font-size: 15px; display: block; }}
      .toc a:hover {{ color: #2563EB; }}
      .btn {{ 
        background-color: #10B981; color: white; padding: 10px 20px; 
        border-radius: 8px; border: none; cursor: pointer; 
        font-weight: 600; font-family: 'Segoe UI', sans-serif; font-size: 14px; 
        width: 100%; text-align: center; transition: background 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      }}
      .btn:hover {{ background-color: #059669; }}
    </style>
    </head>
    <body>
    <div style="position:fixed;left:-9999px;top:0;width:700px;background:white;">
      <div id="{unique_id}">
        {html_content}
      </div>
    </div>
    <button class="btn" onclick="
      var btn = this;
      var originalText = btn.innerHTML;
      btn.innerHTML = '⚙️ Generazione PDF...';
      btn.style.backgroundColor = '#6B7280';
      
      var element = document.getElementById('{unique_id}');
      
      var opt = {{
        margin: [15, 20, 15, 20],
        filename: 'Scenario_{nome_partecipante}.pdf',
        image: {{ type: 'jpeg', quality: 0.98 }},
        html2canvas: {{ scale: 2, useCORS: true, windowWidth: 700, x: 0, y: 0, scrollX: 0, scrollY: 0 }},
        jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
      }};
      
      html2pdf().set(opt).from(element).save().then(function() {{
        btn.innerHTML = originalText;
        btn.style.backgroundColor = '#10B981';
      }});
    ">
      📥 Scarica in PDF
    </button>
    </body>
    </html>
    """
    
    components.html(pdf_html, height=45)

def _build_pdf_quadrant_matrix(sessione, scenari):
    """Genera HTML della matrice 2x2 con assi, frecce e nomi scenari per il PDF."""
    d1p = sessione.get('driver1_pos') or 'Alto'
    d1n = sessione.get('driver1_neg') or 'Basso'
    d2p = sessione.get('driver2_pos') or 'Alto'
    d2n = sessione.get('driver2_neg') or 'Basso'

    sc_map = {s['quadrante']: s for s in scenari}
    def _label(q):
        sc = sc_map.get(q)
        if sc:
            t = sc.get('titolo_finale') or sc.get('titolo')
            if t:
                # Tronca se troppo lungo
                return t[:28] + ('…' if len(t) > 28 else '')
        return q

    return f"""
    <div style="position: relative; width: 280px; height: 230px; margin: 25px auto 35px auto; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <!-- Label Asse Y: top (+) and bottom (-), horizontal -->
      <div style="position: absolute; bottom: calc(100% - 2px); left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: center; max-width: 140px; line-height: 1.2; display: flex; align-items: flex-end; justify-content: center;">{d2p}</div>
      <div style="position: absolute; top: calc(100% - 2px); left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: center; max-width: 140px; line-height: 1.2; display: flex; align-items: flex-start; justify-content: center;">{d2n}</div>
      <!-- Label Asse X: left (-) and right (+), horizontal -->
      <div style="position: absolute; top: 50%; right: calc(100% - 2px); transform: translateY(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: right; max-width: 80px; line-height: 1.2;">{d1n}</div>
      <div style="position: absolute; top: 50%; left: calc(100% + 5px); transform: translateY(-50%); font-size: 10px; font-weight: bold; color: #64748b; text-align: left; max-width: 80px; line-height: 1.2;">{d1p}</div>

      <!-- Quadranti con nomi scenari -->
      <div style="position: absolute; inset: 18px; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 3px;">
        <div style="background: #EEF2FF; border-radius: 6px 0 0 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 5px; font-size: 10px; color: #312E81; font-weight: 600; line-height: 1.3;">{_label('-+')}</div>
        <div style="background: #EEF2FF; border-radius: 0 6px 0 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 5px; font-size: 10px; color: #312E81; font-weight: 600; line-height: 1.3;">{_label('++')}</div>
        <div style="background: #EEF2FF; border-radius: 0 0 0 6px; display: flex; align-items: center; justify-content: center; text-align: center; padding: 5px; font-size: 10px; color: #312E81; font-weight: 600; line-height: 1.3;">{_label('--')}</div>
        <div style="background: #EEF2FF; border-radius: 0 0 6px 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 5px; font-size: 10px; color: #312E81; font-weight: 600; line-height: 1.3;">{_label('+-')}</div>
      </div>

      <!-- Asse Y: linea + freccia SOLO in alto -->
      <div style="position: absolute; left: 50%; top: 8px; bottom: 4px; width: 2px; background: #1e293b; transform: translateX(-50%); z-index: 10;"></div>
      <div style="position: absolute; left: 50%; top: 2px; width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-bottom: 7px solid #1e293b; transform: translateX(-50%); z-index: 10;"></div>
      <!-- Asse X: linea + freccia SOLO a destra -->
      <div style="position: absolute; top: 50%; left: 4px; right: 8px; height: 2px; background: #1e293b; transform: translateY(-50%); z-index: 10;"></div>
      <div style="position: absolute; top: 50%; right: 2px; width: 0; height: 0; border-top: 5px solid transparent; border-bottom: 5px solid transparent; border-left: 7px solid #1e293b; transform: translateY(-50%); z-index: 10;"></div>
    </div>
    """

def st_scarica_pdf_report_finale(sessione, scenari, fenomeni, voti, partecipanti=None):
    sid = sessione["id"]
    fenom_map = {f["id"]: f for f in fenomeni}

    if voti:
        fenomeni_ordinati = [
            (i + 1, fenom_map[v["fenomeno_id"]]["testo"], v["media_posizione"])
            for i, v in enumerate(voti)
            if v["fenomeno_id"] in fenom_map
        ]
    else:
        fenomeni_ordinati = [(i + 1, f["testo"], None) for i, f in enumerate(fenomeni)]

    # ── CSS comune ────────────────────────────────────────────
    CSS = """
      * { box-sizing: border-box; word-wrap: break-word; overflow-wrap: break-word; }
      body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; color: #1F2937; margin: 0; }
      #pdf-body { padding: 24px 32px; max-width: 680px; margin: 0 auto; }
      h1 { color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 12px; margin-bottom: 20px; font-size: 22px; }
      h2 { color: #312E81; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-top: 0; margin-bottom: 16px; font-size: 17px; }
      h3 { color: #4338CA; margin-top: 18px; margin-bottom: 8px; font-size: 14px; }
      p, li { line-height: 1.7; font-size: 13px; }
      strong { color: #111827; }
      blockquote { border-left: 4px solid #4F46E5; padding: 6px 14px; margin-left: 0;
                   color: #4B5563; font-style: italic; background: #F3F4F6; border-radius: 4px; }
      .section { page-break-before: always; padding-top: 8px; }
      .section:first-of-type { page-break-before: avoid; }
      .box { padding: 12px 14px; margin: 10px 0; border-radius: 8px; border-left: 5px solid; page-break-inside: avoid; }
      .box h3 { margin-top: 0; margin-bottom: 8px; font-size: 13px; }
      .box ul { margin: 0; padding-left: 18px; }
      .box.minacce   { background: #FEF2F2; border-color: #EF4444; }
      .box.minacce h3   { color: #991B1B; }
      .box.opportunita { background: #ECFDF5; border-color: #10B981; }
      .box.opportunita h3 { color: #065F46; }
      .box.comune    { background: #EFF6FF; border-color: #3B82F6; }
      .box.comune h3    { color: #1E3A8A; }
      .box.divergenze { background: #FEFCE8; border-color: #EAB308; }
      .box.divergenze h3 { color: #854D0E; }
      .sc-header { background: #E0F2FE; border: 2px solid #0284C7; border-radius: 8px;
                   padding: 14px 20px; margin-bottom: 20px; text-align: center; page-break-after: avoid; }
      .sc-label  { display: block; font-size: 11px; font-weight: 700; color: #0369A1;
                   text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
      .sc-title  { color: #0C4A6E; font-size: 20px; font-weight: 800; margin: 0; }
      .sc-quad   { display: inline-block; margin-top: 8px; background: #BAE6FD; color: #075985;
                   padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
      .toc-item  { display: flex; align-items: center; gap: 12px; padding: 10px 14px;
                   background: #F8FAFC; border-left: 4px solid #94A3B8; border-radius: 4px;
                   margin-bottom: 8px; page-break-inside: avoid; }
      .toc-num   { min-width: 28px; height: 28px; border-radius: 50%; background: #4F46E5;
                   color: white; font-weight: 700; font-size: 12px;
                   display: flex; align-items: center; justify-content: center; }
      .toc-text  { font-size: 13px; color: #334155; }
      .toc-text strong { color: #1e1b4b; }
      .meta-row  { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 6px; }
      .meta-item { font-size: 13px; }
      .meta-label { color: #6B7280; font-size: 11px; text-transform: uppercase;
                    letter-spacing: 0.05em; font-weight: 600; }
      .rank-row  { display: flex; align-items: center; gap: 8px; padding: 5px 0;
                   border-bottom: 1px solid #F3F4F6; }
      .rank-num  { min-width: 22px; height: 22px; border-radius: 50%; color: white;
                   font-size: 10px; font-weight: 700;
                   display: flex; align-items: center; justify-content: center; }
      .rank-text { font-size: 12px; color: #374151; flex: 1; }
      .rank-avg  { font-size: 11px; color: #9CA3AF; }
      .divider   { border: none; border-top: 1px solid #E5E7EB; margin: 16px 0; }
      .btn { background: #4F46E5; color: white; padding: 12px 24px; border-radius: 8px;
             border: none; cursor: pointer; font-weight: 600; font-size: 15px;
             width: 100%; text-align: center; font-family: 'Segoe UI', sans-serif; }
      .btn:hover { background: #4338CA; }
    """

    # ── Costruisce HTML direttamente ──────────────────────────
    s = []

    # — Copertina —
    s.append("<div id='pdf-body'>")
    s.append(f"<h1>📊 Report Foresight — Sessione #{sid}</h1>")
    s.append("<div class='meta-row'>")
    s.append(f"<div class='meta-item'><div class='meta-label'>Domanda di ricerca</div>{_esc(sessione['domanda_ricerca'])}</div>")
    s.append("</div>")
    s.append("<div class='meta-row'>")
    s.append(f"<div class='meta-item'><div class='meta-label'>Orizzonte temporale</div>{_esc(sessione.get('frame_temporale','—'))}</div>")
    s.append(f"<div class='meta-item'><div class='meta-label'>Codice sessione</div><code>{_esc(sessione.get('codice','—'))}</code></div>")
    s.append(f"<div class='meta-item'><div class='meta-label'>Stato</div>{_esc(sessione.get('stato','—'))}</div>")
    s.append("</div>")

    # — Partecipanti —
    if partecipanti:
        s.append("<div class='section'>")
        s.append("<h2>👥 Partecipanti</h2>")
        nomi = ", ".join(_esc(p.get("nome", "?")) for p in partecipanti)
        s.append(f"<p>{nomi}</p>")
        s.append("</div>")

    # — Driver —
    if sessione.get("driver1_nome") or sessione.get("driver2_nome"):
        s.append("<div class='section'>")
        s.append("<h2>🔀 Driver degli Scenari</h2>")
        s.append("<ul>")
        s.append(f"<li><strong>Driver 1:</strong> {_esc(sessione.get('driver1_nome','—'))} "
                 f"(+: {_esc(sessione.get('driver1_pos','?'))} / −: {_esc(sessione.get('driver1_neg','?'))})</li>")
        s.append(f"<li><strong>Driver 2:</strong> {_esc(sessione.get('driver2_nome','—'))} "
                 f"(+: {_esc(sessione.get('driver2_pos','?'))} / −: {_esc(sessione.get('driver2_neg','?'))})</li>")
        s.append("</ul>")
        if sessione.get("driver1_nome"):
            s.append(_build_pdf_quadrant_matrix(sessione, scenari))
        s.append("</div>")

    # — Fenomeni prioritizzati —
    s.append("<div class='section'>")
    s.append("<h2>📋 Fenomeni prioritizzati</h2>")
    COLORI_RANK = ["#7C3AED", "#2563EB", "#0D9488", "#9CA3AF"]
    n_fen = len(fenomeni_ordinati)
    for pos, testo, avg in fenomeni_ordinati:
        tier = min(int((pos - 1) / n_fen * 4), 3) if n_fen else 0
        colore = COLORI_RANK[tier]
        avg_str = f"<span class='rank-avg'>media {avg:.1f}</span>" if avg is not None else ""
        s.append(
            f"<div class='rank-row'>"
            f"<div class='rank-num' style='background:{colore}'>{pos}</div>"
            f"<div class='rank-text'>{_esc(testo)}</div>"
            f"{avg_str}"
            f"</div>"
        )
    s.append("</div>")

    # — Indice scenari —
    if scenari:
        s.append("<div class='section'>")
        s.append("<h2>📑 Indice degli Scenari</h2>")
        for sc in scenari:
            titolo_disp = sc.get("titolo_finale") or sc.get("titolo") or f"Scenario {sc['numero']}"
            s.append(
                f"<div class='toc-item'>"
                f"<div class='toc-num'>{sc['numero']}</div>"
                f"<div class='toc-text'><strong>Scenario {sc['numero']}</strong> — {_esc(titolo_disp)}"
                f"<br><small style='color:#6B7280'>Quadrante: {_esc(sc.get('quadrante',''))}</small></div>"
                f"</div>"
            )
        s.append("</div>")

    # — Scenari —
    for sc in scenari:
        titolo_disp = sc.get("titolo_finale") or sc.get("titolo") or f"Scenario {sc['numero']}"
        t_fin = sc.get("titolo_finale")
        n_fin = sc.get("narrativa_finale")
        m_fin = sc.get("minacce_finale") or []
        o_fin = sc.get("opportunita_finale") or []
        has_final = any([t_fin, n_fin, m_fin, o_fin])

        s.append(f"<div class='section'>")
        s.append(
            f"<div class='sc-header'>"
            f"<span class='sc-label'>Scenario {sc['numero']}</span>"
            f"<div class='sc-title'>{_esc(titolo_disp)}</div>"
            f"<span class='sc-quad'>Quadrante: {_esc(sc.get('quadrante',''))}</span>"
            f"</div>"
        )

        if has_final:
            s.append("<blockquote>Questo scenario è stato discusso ed evoluto dal gruppo partendo da una bozza AI.</blockquote>")
            s.append("<h3>🧠 Versione Definitiva</h3>")
            if n_fin:
                s.append(f"<p>{_esc(n_fin).replace(chr(10), '<br>')}</p>")
            if m_fin:
                items = "".join(f"<li>{_esc(m)}</li>" for m in m_fin)
                s.append(f"<div class='box minacce'><h3>⚠️ Minacce</h3><ul>{items}</ul></div>")
            if o_fin:
                items = "".join(f"<li>{_esc(o)}</li>" for o in o_fin)
                s.append(f"<div class='box opportunita'><h3>✨ Opportunità</h3><ul>{items}</ul></div>")
            s.append("<hr class='divider'>")
            s.append("<h3>🤖 Bozza dell'Agente</h3>")

        if sc.get("narrativa"):
            s.append(f"<p>{_esc(sc['narrativa']).replace(chr(10), '<br>')}</p>")

        if sc.get("key_points_data") and isinstance(sc["key_points_data"], dict):
            kp = sc["key_points_data"]
            std = {k: v for k, v in kp.items() if k not in ("punti_comune", "divergenze")}
            if std:
                items = "".join(f"<li><strong>{_esc(k)}:</strong> {_esc(v)}</li>" for k, v in std.items())
                s.append(f"<h3>🎯 Key Points</h3><ul>{items}</ul>")
            if kp.get("punti_comune"):
                items = "".join(f"<li>{_esc(x)}</li>" for x in kp["punti_comune"])
                s.append(f"<div class='box comune'><h3>🤝 Punti in Comune</h3><ul>{items}</ul></div>")
            if kp.get("divergenze"):
                items = "".join(f"<li>{_esc(x)}</li>" for x in kp["divergenze"])
                s.append(f"<div class='box divergenze'><h3>⚡ Divergenze</h3><ul>{items}</ul></div>")

        if not has_final:
            if sc.get("minacce"):
                items = "".join(f"<li>{_esc(m)}</li>" for m in sc["minacce"])
                s.append(f"<div class='box minacce'><h3>⚠️ Minacce</h3><ul>{items}</ul></div>")
            if sc.get("opportunita"):
                items = "".join(f"<li>{_esc(o)}</li>" for o in sc["opportunita"])
                s.append(f"<div class='box opportunita'><h3>✨ Opportunità</h3><ul>{items}</ul></div>")

        s.append("</div>")  # .section

    s.append("</div>")  # #pdf-body
    html_content = "\n".join(s)

    pdf_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div style="position:absolute;left:0;top:0;width:720px;background:white;opacity:0.01;z-index:-10;pointer-events:none;">
  {html_content}
</div>
<button class="btn" onclick="
  var btn=this;
  btn.innerHTML='⚙️ Generazione in corso...';
  btn.style.background='#6B7280';
  var el=document.getElementById('pdf-body');
  var opt={{
    margin:[15,18,15,18],
    filename:'Report_Foresight_{sid}.pdf',
    image:{{type:'jpeg',quality:0.98}},
    html2canvas:{{scale:2,useCORS:true,windowWidth:720,scrollX:0,scrollY:0}},
    jsPDF:{{unit:'mm',format:'a4',orientation:'portrait'}},
    pagebreak:{{mode:['css','legacy']}}
  }};
  html2pdf().set(opt).from(el).save().then(function(){{
    btn.innerHTML='📥 Scarica Report Finale in PDF';
    btn.style.background='#4F46E5';
  }});
">📥 Scarica Report Finale in PDF</button>
</body>
</html>"""

    components.html(pdf_html, height=65)
    return html_content
