import markdown
import streamlit.components.v1 as components

def st_scarica_pdf_scenario_individuale(scenario_indiv, sessione, nome_partecipante):
    # Genera markdown
    lines = [
        f"# Scenario Individuale — {nome_partecipante}",
        f"",
        f"**Sessione:** {sessione['domanda_ricerca']}",
        f"**Orizzonte temporale:** {sessione['frame_temporale']}",
        f"**Quadrante assegnato:** `{scenario_indiv['quadrante']}`",
        f"",
    ]
    if scenario_indiv.get("titolo"):
        lines += [
            f"<div class='scenario-title-box'>",
            f"  <span class='scenario-label'>Scenario {scenario_indiv['numero']}</span>",
            f"  <h2 class='scenario-name'>{scenario_indiv['titolo']}</h2>",
            f"</div>",
            f""
        ]
    if scenario_indiv.get("narrativa"):
        lines.append(scenario_indiv["narrativa"])
        lines.append("")

    if scenario_indiv.get("key_points_data"):
        lines.append("### Key Points Esplorati")
        for kp, ris in scenario_indiv["key_points_data"].items():
            lines.append(f"- **{kp}:** {ris}")
        lines.append("")

    if scenario_indiv.get("minacce"):
        lines.append("<div class='box minacce'><h4>⚠️ Minacce</h4><ul>")
        for m in scenario_indiv["minacce"]:
            lines.append(f"<li>{m}</li>")
        lines.append("</ul></div>")
        
    if scenario_indiv.get("opportunita"):
        lines.append("<div class='box opportunita'><h4>✨ Opportunità</h4><ul>")
        for o in scenario_indiv["opportunita"]:
            lines.append(f"<li>{o}</li>")
        lines.append("</ul></div>")

    md = "\n".join(lines)
    html_content = markdown.markdown(md)
    
    unique_id = f"pdf-sc-{scenario_indiv['id']}"

    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
      * {{ box-sizing: border-box; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; }}
      body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; color: #333; margin: 0; }}
      #{unique_id} {{ padding: 10px 20px; }}
      #{unique_id} h1 {{ color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 10px; margin-bottom: 20px; }}
      #{unique_id} h3 {{ color: #4338CA; margin-top: 20px; }}
      #{unique_id} p, #{unique_id} li {{ line-height: 1.6; font-size: 14px; position: relative; z-index: 1; }}
      .box {{ padding: 15px; margin-top: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 5px solid; }}
      .box h4 {{ margin-top: 0 !important; margin-bottom: 10px; font-size: 16px; padding-bottom: 5px; }}
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
      .scenario-label {{ display: block; font-size: 14px; font-weight: 700; color: #0369A1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
      .scenario-name {{ color: #0C4A6E !important; margin: 0 !important; padding: 0 !important; border: none !important; font-size: 24px; }}
      .scenario-quadrant {{ display: inline-block; margin-top: 10px; background-color: #BAE6FD; color: #075985; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: 600; }}
      .toc {{ list-style: none; padding-left: 0; margin-bottom: 30px; page-break-after: always; }}
      .toc li {{ margin-bottom: 10px; padding: 12px; background-color: #F8FAFC; border-left: 4px solid #94A3B8; border-radius: 4px; }}
      .toc a {{ text-decoration: none; color: #334155; font-size: 16px; display: block; }}
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
    <div style="position: absolute; left: 0; top: 0; width: 780px; background-color: white; opacity: 0.01; z-index: -10; pointer-events: none;">
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
        margin: 15,
        filename: 'Scenario_{nome_partecipante}.pdf',
        image: {{ type: 'jpeg', quality: 0.98 }},
        html2canvas: {{ scale: 2, useCORS: true, windowWidth: 800, x: 0, y: 0, scrollX: 0, scrollY: 0 }},
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

def st_scarica_pdf_report_finale(sessione, scenari, fenomeni, voti):
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

    lines = [
        f"# Report Foresight — Sessione #{sid}",
        f"",
        f"**Domanda di ricerca:** {sessione['domanda_ricerca']}",
        f"**Orizzonte temporale:** {sessione['frame_temporale']}",
        f"**Codice sessione:** {sessione.get('codice', '—')}",
        f"",
        f"## Driver",
        f"- **Driver 1:** {sessione.get('driver1_nome', '—')} ({sessione.get('driver1_pos', '+')} / {sessione.get('driver1_neg', '−')})",
        f"- **Driver 2:** {sessione.get('driver2_nome', '—')} ({sessione.get('driver2_pos', '+')} / {sessione.get('driver2_neg', '−')})",
        f"",
        f"## Fenomeni prioritizzati",
    ]
    for pos, testo, avg in fenomeni_ordinati:
        avg_str = f" (avg: {avg:.1f})" if avg is not None else ""
        lines.append(f"{pos}. {testo}{avg_str}")

    lines.append("")
    lines.append("## Indice degli Scenari")
    lines.append("<ul class='toc'>")
    for sc in scenari:
        t_fin = sc.get("titolo_finale")
        titolo_orig = sc.get("titolo") or f"Scenario {sc['numero']}"
        titolo_disp = t_fin if t_fin else titolo_orig
        lines.append(f"<li><a href='#scenario-{sc['numero']}'><strong>Scenario {sc['numero']}</strong>: {titolo_disp}</a></li>")
    lines.append("</ul>")

    for sc in scenari:
        titolo_orig = sc.get("titolo") or f"Scenario {sc['numero']}"
        t_fin = sc.get("titolo_finale")
        n_fin = sc.get("narrativa_finale")
        m_fin = sc.get("minacce_finale")
        o_fin = sc.get("opportunita_finale")
        
        has_final = any([t_fin, n_fin, m_fin, o_fin])
        titolo_disp = t_fin if t_fin else titolo_orig

        lines += [
            f"",
            f"<div class='page-break'></div>",
            f"<div class='scenario-title-box' id='scenario-{sc['numero']}'>",
            f"  <span class='scenario-label'>Scenario {sc['numero']}</span>",
            f"  <h2 class='scenario-name'>{titolo_disp}</h2>",
            f"  <span class='scenario-quadrant'>Quadrante: {sc['quadrante']}</span>",
            f"</div>",
        ]
        
        if has_final:
            lines += [
                f"",
                f"> **Nota Storica:** Questo scenario è stato attivamente discusso ed evoluto dai partecipanti partendo da una base AI.",
                f"",
                f"#### 🧠 Versione Definitiva (Consolidata dal Gruppo)"
            ]
            if n_fin:
                lines += [f"", n_fin]
            
            if m_fin:
                lines.append("<div class='box minacce'><h4>⚠️ Minacce</h4><ul>")
                for m in m_fin: lines.append(f"<li>{m}</li>")
                lines.append("</ul></div>")
            if o_fin:
                lines.append("<div class='box opportunita'><h4>✨ Opportunità</h4><ul>")
                for o in o_fin: lines.append(f"<li>{o}</li>")
                lines.append("</ul></div>")
                
            lines.append("")
            lines.append("---")
            lines.append("#### 🤖 Origine: Bozza dell'Agente per la Discussione")
            
        if sc.get("narrativa"):
            lines += [f"", sc["narrativa"]]
        if sc.get("key_points_data"):
            kp_data = sc["key_points_data"]
            if isinstance(kp_data, dict):
                p_com = kp_data.get("punti_comune", [])
                divs = kp_data.get("divergenze", [])
                standard_kp = {k: v for k, v in kp_data.items() if k not in ("punti_comune", "divergenze")}
                
                if standard_kp:
                    lines.append("")
                    lines.append("**Key Points:**")
                    for k, v in standard_kp.items():
                        lines.append(f"- **{k}:** {v}")
                
                if p_com:
                    lines.append("<div class='box comune'><h4>🤝 Punti in Comune</h4><ul>")
                    for x in p_com: lines.append(f"<li>{x}</li>")
                    lines.append("</ul></div>")
                    
                if divs:
                    lines.append("<div class='box divergenze'><h4>⚡ Divergenze Emerse</h4><ul>")
                    for x in divs: lines.append(f"<li>{x}</li>")
                    lines.append("</ul></div>")
        
        if not has_final:
            if sc.get("minacce"):
                lines.append("<div class='box minacce'><h4>⚠️ Minacce</h4><ul>")
                for m in sc["minacce"]:
                    lines.append(f"<li>{m}</li>")
                lines.append("</ul></div>")
            if sc.get("opportunita"):
                lines.append("<div class='box opportunita'><h4>✨ Opportunità</h4><ul>")
                for o in sc["opportunita"]:
                    lines.append(f"<li>{o}</li>")
                lines.append("</ul></div>")

    md = "\n".join(lines)
    html_content = markdown.markdown(md)

    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
      * {{ box-sizing: border-box; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; }}
      body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; color: #333; margin: 0; }}
      #pdf-report-body {{ padding: 10px 20px; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
      #pdf-report-body h1 {{ color: #4F46E5; border-bottom: 2px solid #e0e7ff; padding-bottom: 15px; margin-bottom: 25px; page-break-after: avoid; }}
      #pdf-report-body h2 {{ color: #312E81; margin-top: 35px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; page-break-after: avoid; }}
      #pdf-report-body h3 {{ color: #4338CA; margin-top: 25px; margin-bottom: 10px; page-break-after: avoid; }}
      #pdf-report-body h4 {{ color: #111827; margin-top: 20px; page-break-after: avoid; }}
      #pdf-report-body p, #pdf-report-body li {{ line-height: 1.7; font-size: 15px; }}
      #pdf-report-body strong {{ color: #111827; }}
      #pdf-report-body blockquote {{ border-left: 4px solid #4F46E5; padding-left: 15px; margin-left: 0; padding-top: 5px; padding-bottom: 5px; color: #4B5563; font-style: italic; background-color: #F3F4F6; border-radius: 4px; }}
      .page-break {{ page-break-before: always; }}
      .box {{ padding: 15px; margin-top: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 5px solid; page-break-inside: avoid; }}
      .box h4 {{ margin-top: 0 !important; margin-bottom: 10px; font-size: 16px; padding-bottom: 5px; }}
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
      .scenario-label {{ display: block; font-size: 14px; font-weight: 700; color: #0369A1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
      .scenario-name {{ color: #0C4A6E !important; margin: 0 !important; padding: 0 !important; border: none !important; font-size: 24px; }}
      .scenario-quadrant {{ display: inline-block; margin-top: 10px; background-color: #BAE6FD; color: #075985; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: 600; }}
      .toc {{ list-style: none; padding-left: 0; margin-bottom: 30px; page-break-after: always; }}
      .toc li {{ margin-bottom: 10px; padding: 12px; background-color: #F8FAFC; border-left: 4px solid #94A3B8; border-radius: 4px; }}
      .toc a {{ text-decoration: none; color: #334155; font-size: 16px; display: block; }}
      .toc a:hover {{ color: #2563EB; }}
      .btn {{ 
        background-color: #4F46E5; color: white; padding: 12px 24px; 
        border-radius: 8px; border: none; cursor: pointer; 
        font-weight: 600; font-family: 'Segoe UI', sans-serif; font-size: 15px; 
        width: 100%; text-align: center; transition: background 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      }}
      .btn:hover {{ background-color: #4338CA; }}
    </style>
    </head>
    <body>

    <div style="position: absolute; left: 0; top: 0; width: 780px; background-color: white; opacity: 0.01; z-index: -10; pointer-events: none;">
      <div id="pdf-report-body">
        {html_content}
      </div>
    </div>

    <button class="btn" onclick="
      var btn = this;
      var originalText = btn.innerHTML;
      btn.innerHTML = '⚙️ Generazione PDF in corso...';
      btn.style.backgroundColor = '#6B7280';
      
      var element = document.getElementById('pdf-report-body');
      
      var opt = {{
        margin: [10, 10, 10, 10],
        filename: 'Report_Scenario_Planning_#{sid}.pdf',
        image: {{ type: 'jpeg', quality: 0.98 }},
        html2canvas: {{ scale: 2, useCORS: true, windowWidth: 780, windowHeight: window.innerHeight, x: 0, y: 0, scrollX: 0, scrollY: 0 }},
        jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }},
        pagebreak: {{ mode: ['avoid-all', 'css', 'legacy'] }},
        enableLinks: true
      }};
      
      html2pdf().set(opt).from(element).save().then(function() {{
        btn.innerHTML = originalText;
        btn.style.backgroundColor = '#4F46E5';
      }});
    ">
      📥 Scarica Report Finale in PDF Reale
    </button>
    </body>
    </html>
    """

    components.html(pdf_html, height=65)
    return md
