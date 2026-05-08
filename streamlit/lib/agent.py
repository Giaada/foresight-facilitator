import anthropic
import os
import json
import re
from .database import get_messaggi, aggiungi_messaggio, aggiorna_scenario


STEP_ORDINE = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"]


def _get_client():
    """Crea il client Anthropic leggendo la chiave da secrets o env al momento della chiamata."""
    try:
        import streamlit as st
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=api_key)


def descrivi_quadrante(quadrante, d1_nome, d1_pos, d1_neg, d2_nome, d2_pos, d2_neg):
    asse_x = d1_pos if quadrante[0] == "+" else d1_neg
    asse_y = d2_pos if quadrante[1] == "+" else d2_neg
    asse_x = asse_x or ("alto" if quadrante[0] == "+" else "basso")
    asse_y = asse_y or ("alto" if quadrante[1] == "+" else "basso")
    d1 = d1_nome or "Driver 1"
    d2 = d2_nome or "Driver 2"
    return f"{d1}: {asse_x} × {d2}: {asse_y}"


def sistema_prompt(scenario, sessione, key_points):
    """
    Restituisce il system prompt come lista di blocchi per l'API Anthropic.
    Il primo blocco (statico per tutta la sessione) è marcato con cache_control:
    i token in cache vengono addebitati al 10% del normale, riducendo il TPM
    consumato e abbassando la latenza per le chiamate successive.
    Il secondo blocco contiene solo lo step corrente (l'unico elemento variabile)
    e non viene cachato.
    """
    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    kp_list = ", ".join(key_points) if key_points else "nessun key point definito"
    step = scenario["step_corrente"]

    kp_primo = key_points[0] if key_points else "Key Point 1"
    kp_esempio = ", ".join(f'"{kp}": "sintesi della risposta del partecipante"' for kp in (key_points[:2] if key_points else ["Key Point 1"]))

    static_text = f"""Sei un esperto facilitatore di Strategic Foresight.
Stai guidando la costruzione di uno scenario futuro.

CONTESTO:
- Domanda di ricerca: "{sessione['domanda_ricerca']}"
- Orizzonte temporale: {sessione['frame_temporale']}
- Scenario assegnato: {descrizione}

KEY POINTS da esplorare: {kp_list}

FLUSSO DA SEGUIRE (lo step corrente è indicato alla fine di questo prompt):
1. intro → presenta il quadrante in modo coinvolgente e fai subito la prima domanda aperta sul primo key point; non spiegare l'intero percorso in anticipo
2. key_points → esplora ogni key point ({kp_list}) uno alla volta in modo conversazionale; per ogni key point fai una domanda aperta e poi approfondisci con 1-2 domande di follow-up per far emergere ragionamenti concreti, esempi, implicazioni; non esaurire il tema in un solo scambio ma non dilungarti oltre 3 turni per key point; quando hai materiale sufficiente su un tema passa naturalmente al successivo senza annunciarlo; accumula le risposte in key_points_data
3. narrativa → scrivi nel campo "testo" un messaggio discorsivo che: (a) introduce brevemente cosa stai per fare, (b) riporta la narrativa completa dello scenario (3-5 frasi di prosa continua, in prima persona plurale "In questo scenario..."), (c) chiede al partecipante se la narrativa lo convince o vuole modificare qualcosa. La stessa narrativa va anche in aggiornamenti.narrativa. NON usare elenchi o intestazioni nella narrativa: solo paragrafo continuo.
4. titolo → chiedi un titolo; se non fornito, suggerisci 3 opzioni
5. minacce → chiedi al partecipante quali minacce e rischi vede in questo scenario; ascolta, fai domande di chiarimento se serve, ma NON suggerire minacce tu stesso; REGOLA CRITICA: in OGNI tuo messaggio di questo step includi in aggiornamenti.minacce l'elenco COMPLETO e AGGIORNATO di tutte le minacce emerse finora, anche durante le domande di follow-up; non lasciare mai aggiornamenti.minacce vuoto se hai già raccolto minacce
6. opportunita → chiedi al partecipante quali opportunità vede in questo scenario; ascolta, fai domande di chiarimento se serve, ma NON suggerire opportunità tu stesso; REGOLA CRITICA: in OGNI tuo messaggio di questo step includi in aggiornamenti.opportunita l'elenco COMPLETO e AGGIORNATO di tutte le opportunità emerse finora; includi anche aggiornamenti.minacce con i valori già salvati in precedenza (non lasciarli null)
7. concluso → raccordi e sintetizzi tutte le idee emerse nel dialogo: fai un riepilogo narrativo completo (titolo, narrativa, minacce, opportunità), evidenzia i fili conduttori e le tensioni più interessanti che sono emersi nella conversazione, poi saluta calorosamente

COERENZA CON LO SCENARIO (REGOLA PRIORITARIA):
- Lo scenario assegnato è "{descrizione}". Questo definisce un mondo ipotetico preciso: i due driver hanno quei valori, non altri.
- Se il partecipante fornisce una risposta che presuppone condizioni opposte o incompatibili con lo scenario (es. descrive un'alta adozione tecnologica in uno scenario di bassa adozione, o un clima di fiducia elevata in uno scenario di sfiducia), NON accettare la risposta come valida.
- In questo caso, nel campo "testo" riconosci brevemente il contributo del partecipante, poi reindirizzalo con gentilezza ma chiarezza: ricordagli in quale scenario si trova, spiega cosa implica quel quadrante, e riformula la domanda chiedendogli di ragionare DENTRO quel contesto specifico.
- Non avanzare di step e non salvare in key_points_data una risposta incoerente: aspetta una risposta che sia compatibile con lo scenario.

ISTRUZIONI E COMPORTAMENTO:
- Comunica in italiano nel campo "testo". Tale campo DEVE essere prosa discorsiva, empatica e colloquiale: scrivi come parlerebbe un facilitatore esperto in una conversazione vera. VIETATO usare elenchi puntati, elenchi numerati, titoli in grassetto, trattini o qualsiasi struttura visiva nel campo "testo". Solo frasi e paragrafi.
- Privilegia le domande alle affermazioni: il tuo ruolo è far emergere il pensiero del partecipante, non condividerlo tu stesso. Evita frasi del tipo "In questo scenario potremmo vedere...", "Un aspetto interessante è...", "Immagino che..." se quelle idee non sono state dette dal partecipante: aspetta che sia lui/lei a proporre, poi esplora con domande.
- NON ricapitolare ciò che il partecipante ha già detto ad ogni turno: la conversazione scorre, non serve ripetere.
- Fai UNA sola domanda o richiesta alla volta, in modo chiaro. Ma non fermarti al primo scambio: il tuo ruolo è spronare il partecipante ad andare in profondità, a portare esempi concreti, a ragionare sulle implicazioni. Una risposta breve o generica va sempre esplorata con una domanda di follow-up.
- Sii specifico rispetto all'orizzonte temporale {sessione['frame_temporale']}.
- Termina SEMPRE il campo "testo" con una domanda concreta o una richiesta esplicita all'utente. Non lasciare mai il messaggio senza una call-to-action.
- Quando hai raccolto materiale sufficiente su uno step, avanza naturalmente al successivo: segnala la transizione con una frase di raccordo nel testo (es. "Bene, costruiamo ora la narrativa dello scenario..." oppure "Passiamo al titolo...") e imposta "nuovo_step" al nome dello step successivo. Non attendere una conferma esplicita dell'utente: sei tu il facilitatore e guidi il ritmo. Se il partecipante vuole tornare su qualcosa di precedente, ascolta e poi riprendi il filo.

REGOLE PER aggiornamenti (FONDAMENTALE - segui sempre):
- Dato che sei in un'App, l'interfaccia utente mostra i dati in tempo reale SOLO SE fornisci l'oggetto "aggiornamenti" completo ad OGNI singolo messaggio.
- Ad OGNI tuo messaggio DEVI SEMPRE RIPETERE tutti i dati accumulati precedentemente (narrativa parziale, minacce, etc.) dentro l'oggetto 'aggiornamenti'. Non mettere mai null se hai già raccolto una narrativa o un titolo: COPIALO e ripetilo per mantenere l'interfaccia sincronizzata!
- Step key_points: salva e accumula in tempo reale tutte le risposte ricevute in aggiornamenti.key_points_data usando ESATTAMENTE i nomi dei key points come chiavi ({kp_list}), non nomi generici come "nome_key_point_1".

RISPOSTA — REGOLE ASSOLUTE:
- INIZIA LA RISPOSTA DIRETTAMENTE CON {{ — NESSUN TESTO PRIMA, NESSUN MARKDOWN, NESSUN ```json
- TERMINA CON }}
- NESSUN CARATTERE AL DI FUORI DEL JSON
- Se sei nello step "narrativa", aggiornamenti.narrativa DEVE contenere la narrativa per esteso (non null): è obbligatorio, altrimenti il lavoro del partecipante va perso.

{{
  "testo": "il vero messaggio discorsivo che leggerà il partecipante",
  "nuovo_step": "nome del prossimo step se l'utente ti ha autorizzato ad avanzare, altrimenti null",
  "aggiornamenti": {{
    "narrativa": "testo narrativa accumulato fino ad ora se disponibile, altrimenti null",
    "titolo": "titolo stabilito o provvisorio se confermato/impostato, altrimenti null",
    "minacce": ["minaccia emersa 1", "minaccia 2"],
    "opportunita": ["opportunità 1"],
    "key_points_data": {{{kp_esempio}}}
  }}
}}"""

    return [
        {
            "type": "text",
            "text": static_text,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"STEP CORRENTE: {step}",
        },
    ]


def _extract_testo(contenuto):
    """Estrae il testo leggibile da un messaggio che contiene JSON grezzo."""
    if not contenuto or not contenuto.strip().startswith('{') or '"testo"' not in contenuto:
        return contenuto
    try:
        return json.loads(contenuto).get("testo") or contenuto
    except Exception:
        m = re.search(r'"testo"\s*:\s*"((?:[^"\\]|\\.)*)"', contenuto)
        if m:
            return m.group(1).replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
    return contenuto


def _build_history(messaggi_db, testo_utente):
    """
    Costruisce la history per l'API Anthropic.
    L'API richiede che il primo messaggio sia sempre 'user'.
    Se la history dal DB inizia con 'assistant' (messaggio di benvenuto),
    aggiungiamo un messaggio utente fittizio di apertura.
    I messaggi assistant con JSON grezzo (es. da risposte troncate) vengono
    ripuliti per non confondere il modello.
    """
    msgs = []
    for m in messaggi_db:
        content = _extract_testo(m["contenuto"]) if m["ruolo"] == "assistant" else m["contenuto"]
        msgs.append({"role": m["ruolo"], "content": content})

    msgs.append({"role": "user", "content": testo_utente})

    # Garantisce alternanza corretta user/assistant richiesta dall'API
    if msgs and msgs[0]["role"] == "assistant":
        msgs = [{"role": "user", "content": "[Sessione avviata]"}] + msgs

    return msgs


def _parse_json(testo_raw):
    """Prova più strategie per estrarre un JSON dalla risposta del modello."""
    # 1. Parse diretto
    try:
        return json.loads(testo_raw.strip())
    except Exception:
        pass
    # 2. Regex {…} (gestisce testo prima/dopo)
    match = re.search(r'\{.*\}', testo_raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # 3. Strip blocchi markdown ```json … ```
    cleaned = re.sub(r'^```(?:json)?\s*', '', testo_raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned.strip())
    except Exception:
        pass
    # 4. JSON dentro code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', testo_raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return None


def invia_messaggio(scenario, sessione, testo_utente):
    """Invia un messaggio e ottieni la risposta dell'agente."""
    key_points = sessione.get("key_points", [])
    messaggi_db = get_messaggi(scenario["id"])
    history = _build_history(messaggi_db, testo_utente)

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=sistema_prompt(scenario, sessione, key_points),
            messages=history,
        )
        testo_raw = risposta.content[0].text

        testo_risposta = testo_raw
        nuovo_step = None
        agg = {}

        parsed = _parse_json(testo_raw)
        if parsed:
            testo_risposta = parsed.get("testo") or testo_raw
            nuovo_step = parsed.get("nuovo_step")
            agg = parsed.get("aggiornamenti") or {
                "narrativa": parsed.get("narrativa"),
                "titolo": parsed.get("titolo"),
                "minacce": parsed.get("minacce", []),
                "opportunita": parsed.get("opportunita", []),
                "key_points_data": parsed.get("key_points_data", {})
            }

        # Safety net: se _parse_json ha fallito ma il testo sembra JSON, riprova estraendo
        # sia il campo "testo" che gli "aggiornamenti" con un approccio più aggressivo
        if not parsed and testo_raw.strip().startswith('{'):
            m_json = re.search(r'\{.*\}', testo_raw, re.DOTALL)
            if m_json:
                try:
                    import json as _json
                    fallback = _json.loads(m_json.group(0))
                    testo_risposta = fallback.get("testo") or testo_risposta
                    nuovo_step = fallback.get("nuovo_step")
                    agg = fallback.get("aggiornamenti") or {}
                except Exception:
                    # ultimo tentativo: estrai almeno il campo testo con regex
                    m = re.search(r'"testo"\s*:\s*"((?:[^"\\]|\\.)*)"', testo_raw)
                    if m:
                        testo_risposta = m.group(1).replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')

        # Fallback narrativa: il modello a volte scrive la narrativa nel campo "testo"
        # ma dimentica di duplicarla in aggiornamenti.narrativa.
        # Se siamo nello step "narrativa" e il campo è vuoto, la estraiamo dal testo.
        if scenario.get("step_corrente") == "narrativa" and not agg.get("narrativa") and testo_risposta:
            nar_match = re.search(r'(In questo scenario[\s,\u2019\u2018].{80,})', testo_risposta, re.DOTALL | re.IGNORECASE)
            if nar_match:
                nar_text = nar_match.group(1)
                stop = re.search(r'\n\n', nar_text)
                if stop and stop.start() > 100:
                    nar_text = nar_text[:stop.start()]
                if len(nar_text.strip()) > 80:
                    agg["narrativa"] = nar_text.strip()

        # Salva SOLO messaggio assistant (quello user l'ha già salvato la view)
        aggiungi_messaggio(scenario["id"], "assistant", testo_risposta)

        # Aggiorna scenario.
        # Ogni campo viene scritto nel DB SOLO durante lo step dedicato: il modello
        # è istruito a ripetere tutti gli aggiornamenti ad ogni messaggio (per la UI),
        # ma accettare quelle ripetizioni su step sbagliati può sovrascrivere dati
        # corretti con valori errati (es. modello mette testo discorsivo in narrativa
        # durante lo step titolo).
        step = scenario.get("step_corrente", "")

        # Fallback keyword-based step advancement: se il modello non ha impostato
        # nuovo_step nel JSON, controlla se la domanda finale del messaggio segnala
        # una transizione (es. "parliamo delle minacce?")
        if not nuovo_step:
            tl = testo_risposta.lower()
            last_part = tl[len(tl) // 2:]
            _KEYWORD_TRIGGERS = [
                ("key_points", ["narrativa", "costruiamo", "proviamo a costruire", "passiamo alla sintesi"], "narrativa"),
                ("narrativa",  ["titolo", "come lo chiameresti", "nome dello scenario", "come chiamereste"], "titolo"),
                ("titolo",     ["minacce", "minaccia", "rischi", "pericoli"], "minacce"),
                ("minacce",    ["opportunità", "opportunita", "possibilità positive", "potenzialità"], "opportunita"),
            ]
            for _cur, _kws, _next in _KEYWORD_TRIGGERS:
                if step == _cur and any(kw in last_part for kw in _kws):
                    nuovo_step = _next
                    break

        updates = {}
        if nuovo_step and nuovo_step in STEP_ORDINE:
            updates["step_corrente"] = nuovo_step
        if agg.get("narrativa") and step == "narrativa":
            updates["narrativa"] = agg["narrativa"]
        if agg.get("titolo") and step == "titolo":
            updates["titolo"] = agg["titolo"]
        if agg.get("minacce"):
            # salva durante lo step minacce, oppure come fallback durante opportunita/concluso
            # se le minacce non sono ancora state salvate nel DB
            if step == "minacce" or (step in ("opportunita", "concluso") and not scenario.get("minacce")):
                updates["minacce"] = agg["minacce"]
        if agg.get("opportunita"):
            if step == "opportunita" or (step == "concluso" and not scenario.get("opportunita")):
                updates["opportunita"] = agg["opportunita"]
        if agg.get("key_points_data") and step == "key_points":
            kpd = scenario.get("key_points_data", {}) or {}
            kpd.update(agg["key_points_data"])
            updates["key_points_data"] = kpd
        if updates:
            aggiorna_scenario(scenario["id"], **updates)

        return testo_risposta, nuovo_step

    except anthropic.AuthenticationError:
        msg = "⚠️ Chiave API Anthropic non valida o non configurata. Contatta il facilitatore."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except anthropic.RateLimitError:
        msg = "⚠️ Limite di richieste API raggiunto. Attendi qualche secondo e riprova."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except anthropic.APIConnectionError:
        msg = "⚠️ Impossibile connettersi all'API. Verifica la connessione internet."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except anthropic.APIStatusError as e:
        msg = f"⚠️ Errore API ({e.status_code}): {str(e.message)[:200]}"
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except Exception as e:
        msg = f"⚠️ Errore imprevisto ({type(e).__name__}): {str(e)[:300]}"
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None


def avvia_scenario(scenario, sessione):
    """Messaggio iniziale dell'agente per un nuovo scenario.
    Usa il system prompt completo (con caching) per coerenza con invia_messaggio
    e per riscaldare la cache fin dalla prima chiamata.
    """
    key_points = sessione.get("key_points", [])
    kp_str = ", ".join(key_points) if key_points else "tutti gli aspetti rilevanti"
    primo_kp = key_points[0] if key_points else "il contesto generale"

    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )

    prompt = (
        f"Sei nella fase intro. Genera il messaggio di benvenuto per lo Scenario {scenario['numero']}. "
        f"Il messaggio deve essere caldo, coinvolgente e ben articolato (almeno 4-5 frasi). "
        f"Struttura il messaggio così: (1) accogli il partecipante e contestualizza lo scenario '{descrizione}' "
        f"spiegando brevemente cosa implica questo quadrante in relazione alla domanda di ricerca; "
        f"(2) accenna — senza elencarli — che esploreremo insieme questi temi: {kp_str}; "
        f"(3) lancia subito la prima domanda aperta sul primo tema: '{primo_kp}', "
        f"formulandola in modo specifico rispetto all'orizzonte temporale {sessione['frame_temporale']} "
        f"e al quadrante assegnato. "
        f"Tono: colloquiale, empatico, da facilitatore esperto. Nessun elenco. Solo prosa fluente. "
        f"Segui il formato JSON del system prompt."
    )

    client = _get_client()
    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=sistema_prompt(scenario, sessione, key_points),
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        testo_raw = risposta.content[0].text
        parsed = _parse_json(testo_raw)
        testo = (parsed.get("testo") if parsed else None) or ""
        if not testo:
            raise ValueError("campo testo mancante")
    except Exception as e:
        print(f"Errore avvia_scenario: {e}")
        descrizione = descrivi_quadrante(
            scenario["quadrante"],
            sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
            sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
        )
        testo = (
            f"Benvenuti allo Scenario {scenario['numero']}!\n\n"
            f"Lavorerete sul quadrante: **{descrizione}**\n\n"
            f"Insieme esploreremo: {kp_str}\n\n"
            f"Iniziamo: {primo_kp}"
        )

    aggiungi_messaggio(scenario["id"], "assistant", testo)
    aggiorna_scenario(scenario["id"], step_corrente="key_points")
    return testo


def unisci_scenari_gruppo(scenario_gruppo, sessione, scenari_individuali):
    """
    Produce una bozza unica a partire dalle bozze individuali dei partecipanti
    di un determinato quadrante, evidenziando similitudini e differenze.
    Salva il risultato nel record `scenario_gruppo` e lo pone in stato concluso.
    """
    if not scenari_individuali:
        aggiorna_scenario(scenario_gruppo["id"], narrativa="Nessun contributo individuale trovato per questo gruppo.", step_corrente="intro")
        return

    descrizione_quad = descrivi_quadrante(
        scenario_gruppo["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    
    # Prepara il dump delle bozze
    testo_bozze = ""
    for i, s in enumerate(scenari_individuali):
        titolo = s.get("titolo") or f"Idea {i+1}"
        narrativa = s.get("narrativa") or "Nessuna narrativa"
        minacce = ", ".join(s.get("minacce", [])) or "Nessuna"
        opp = ", ".join(s.get("opportunita", [])) or "Nessuna"
        
        testo_bozze += f"\n--- CONTRIBUTO {i+1} ---\nTitolo: {titolo}\nNarrativa: {narrativa}\nMinacce: {minacce}\nOpportunità: {opp}\n"

    prompt = f"""Sei un facilitatore esperto. Devi redigere la BOZZA CONSOLIDATA per lo scenario del Quadrante: {descrizione_quad}.
Orizzonte: {sessione['frame_temporale']}

Hai ricevuto {len(scenari_individuali)} contributi autonomi dai membri di questo gruppo:
{testo_bozze}

IL TUO COMPITO:
Leggi attentamente tutti i contributi e crea uno Scenario Integrato che rappresenti una sintesi potente. 

Rispondi SOLO con un JSON con la seguente struttura:
{{
  "titolo": "Titolo Unificato dello Scenario",
  "narrativa": "Due o tre paragrafi che descrivono coerentemente il mondo futuro integrando le visioni. NON elencare i punti in comune o divergenze qui dentro.",
  "minacce": ["minaccia unificata 1", "minaccia 2", "ecc"],
  "opportunita": ["opportunità unificata 1", "opportunità 2", "ecc"],
  "punti_comune": ["Punto in comune solido 1", "Punto in comune 2"],
  "divergenze": ["Spunto unico di un partecipante 1", "Visione discordante 2"]
}}"""

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system="Sei un facilitatore imparziale capace di fare eccellenti sintesi analitiche. Rispondi SEMPRE E SOLO con un JSON valido.",
            messages=[{"role": "user", "content": prompt}]
        )
        testo_raw = risposta.content[0].text
        cleaned = re.sub(r'^```(?:json)?\s*', '', testo_raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
        
        dati = json.loads(cleaned)
        aggiorna_scenario(
            scenario_gruppo["id"],
            titolo=dati.get("titolo", "Titolo Generato"),
            narrativa=dati.get("narrativa", "Sintesi non disponibile."),
            minacce=dati.get("minacce", []),
            opportunita=dati.get("opportunita", []),
            key_points_data={
                "punti_comune": dati.get("punti_comune", []),
                "divergenze": dati.get("divergenze", [])
            },
            step_corrente="intro"
        )
    except Exception as e:
        aggiorna_scenario(
            scenario_gruppo["id"],
            narrativa=f"Errore durante la generazione della sintesi: {str(e)}",
            step_corrente="intro"
        )

