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
    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    kp_list = ", ".join(key_points) if key_points else "nessun key point definito"
    step = scenario["step_corrente"]

    return f"""Sei un esperto facilitatore di Strategic Foresight.
Stai guidando la costruzione di uno scenario futuro.

CONTESTO:
- Domanda di ricerca: "{sessione['domanda_ricerca']}"
- Orizzonte temporale: {sessione['frame_temporale']}
- Scenario assegnato: {descrizione}

KEY POINTS da esplorare: {kp_list}
STEP CORRENTE: {step}

FLUSSO DA SEGUIRE:
1. intro → presenta il quadrante, invita a iniziare
2. key_points → esplora ogni key point uno alla volta con domande mirate
3. narrativa → sintetizza una descrizione narrativa coerente (3-5 frasi)
4. titolo → chiedi un titolo; se non fornito, suggerisci 3 opzioni
5. minacce → guida l'identificazione delle principali minacce (lista)
6. opportunita → guida l'identificazione delle opportunità (lista)
7. concluso → riepilogo e chiusura

ISTRUZIONI E COMPORTAMENTO:
- Comunica in italiano nel campo "testo". Tale campo DEVE sempre contenere un linguaggio naturale, discorsivo, empatico e umano (evita elenchi puntati freddi, parla come un vero facilitatore).
- Fai UNA sola domanda o richiesta alla volta, in modo chiaro.
- Sii specifico rispetto all'orizzonte temporale {sessione['frame_temporale']}.
- PRIMA di avanzare allo step successivo (ovvero prima di cambiare il campo "nuovo_step"), quando pensi di avere raccolto abbastanza materiale, DEVI CHIEDERE ESPLICITAMENTE all'utente: "Posso procedere [con la sintesi / al prossimo step] o vuoi aggiungere altro?". 
- SOLO se l'utente ti dà la conferma di procedere, al turno successivo imposterai "nuovo_step" al nome dello step seguente. Finché non hai il via libera esplicito, mantieni "nuovo_step" a null e continua la fase corrente.

REGOLE PER aggiornamenti (FONDAMENTALE - segui sempre):
- Dato che sei in una chat interattiva, l'interfaccia utente si aggiorna in tempo reale SOLO SE fornisci il blocco aggiornamenti completo ad ogni singolo tuo messaggio. 
- Ad OGNI tuo messaggio, produci sempre l'intero stato corrente compilato dentro l'oggetto 'aggiornamenti' (narrativa parziale/completa, minacce emerse finora, ecc.).
- MANTIENI SEMPRE il testo dei turni precedenti nei vari campi, non svuotarli, ma semplicemente ammodionali.
- Step key_points: salva/aggiungi tutte le risposte ricevute in aggiornamenti.key_points_data

RISPOSTA - rispondi SOLO con questo JSON, senza testo prima o dopo:
{{
  "testo": "messaggio da mostrare ai partecipanti",
  "nuovo_step": "nome del prossimo step se stai avanzando, altrimenti null",
  "aggiornamenti": {{
    "narrativa": "testo narrativa se disponibile, altrimenti null",
    "titolo": "titolo se confermato, altrimenti null",
    "minacce": ["minaccia 1", "minaccia 2"],
    "opportunita": ["opportunità 1", "opportunità 2"],
    "key_points_data": {{"nome_key_point": "risposta ricevuta"}}
  }}
}}"""


def _build_history(messaggi_db, testo_utente):
    """
    Costruisce la history per l'API Anthropic.
    L'API richiede che il primo messaggio sia sempre 'user'.
    Se la history dal DB inizia con 'assistant' (messaggio di benvenuto),
    aggiungiamo un messaggio utente fittizio di apertura.
    """
    msgs = [{"role": m["ruolo"], "content": m["contenuto"]} for m in messaggi_db]
    msgs.append({"role": "user", "content": testo_utente})

    # Garantisce alternanza corretta user/assistant richiesta dall'API
    if msgs and msgs[0]["role"] == "assistant":
        msgs = [{"role": "user", "content": "[Sessione avviata]"}] + msgs

    return msgs


def invia_messaggio(scenario, sessione, testo_utente):
    """Invia un messaggio e ottieni la risposta dell'agente."""
    key_points = sessione.get("key_points", [])
    messaggi_db = get_messaggi(scenario["id"])
    history = _build_history(messaggi_db, testo_utente)

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=sistema_prompt(scenario, sessione, key_points),
            messages=history,
        )
        testo_raw = risposta.content[0].text

        # Prova a parsare JSON — gestisce blocchi ```json...``` e testo extra
        testo_risposta = testo_raw
        nuovo_step = None
        agg = {}
        try:
            # Rimuovi eventuale blocco markdown ```json ... ```
            cleaned = re.sub(r'^```(?:json)?\s*', '', testo_raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
            # Cerca il primo oggetto JSON completo (non greedy non funziona su oggetti annidati,
            # usiamo json.JSONDecoder.raw_decode che si ferma al termine del primo oggetto valido)
            decoder = json.JSONDecoder()
            idx = cleaned.find('{')
            if idx != -1:
                parsed, _ = decoder.raw_decode(cleaned, idx)
                testo_risposta = parsed.get("testo") or testo_raw
                nuovo_step = parsed.get("nuovo_step")
                agg = parsed.get("aggiornamenti") or {}
        except Exception:
            # Fallback: usa il testo grezzo come risposta
            testo_risposta = testo_raw

        # Salva messaggi
        aggiungi_messaggio(scenario["id"], "user", testo_utente)
        aggiungi_messaggio(scenario["id"], "assistant", testo_risposta)

        # Aggiorna scenario
        updates = {}
        if nuovo_step and nuovo_step in STEP_ORDINE:
            updates["step_corrente"] = nuovo_step
        if agg.get("narrativa"):
            updates["narrativa"] = agg["narrativa"]
        if agg.get("titolo"):
            updates["titolo"] = agg["titolo"]
        if agg.get("minacce"):
            updates["minacce"] = agg["minacce"]
        if agg.get("opportunita"):
            updates["opportunita"] = agg["opportunita"]
        if agg.get("key_points_data"):
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
    except anthropic.APIConnectionError:
        msg = "⚠️ Impossibile connettersi all'API. Verifica la connessione internet."
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None
    except Exception as e:
        msg = f"⚠️ Errore dell'agente: {str(e)}"
        aggiungi_messaggio(scenario["id"], "assistant", msg)
        return msg, None


def avvia_scenario(scenario, sessione):
    """Messaggio iniziale dell'agente per un nuovo scenario."""
    descrizione = descrivi_quadrante(
        scenario["quadrante"],
        sessione.get("driver1_nome"), sessione.get("driver1_pos"), sessione.get("driver1_neg"),
        sessione.get("driver2_nome"), sessione.get("driver2_pos"), sessione.get("driver2_neg"),
    )
    key_points = sessione.get("key_points", [])
    kp_str = ", ".join(key_points) if key_points else "tutti gli aspetti rilevanti"

    prompt = f"""Genera il messaggio di benvenuto per lo Scenario {scenario['numero']}.
Quadrante: {descrizione}
Domanda di ricerca: "{sessione['domanda_ricerca']}"
Orizzonte: {sessione['frame_temporale']}
Key points da esplorare: {kp_str}

Il messaggio deve:
1. Presentare il quadrante in modo coinvolgente
2. Spiegare brevemente il percorso (esploreremo insieme {kp_str})
3. Fare la prima domanda sul primo key point: "{key_points[0] if key_points else 'il contesto generale'}"

Rispondi SOLO con il testo del messaggio, in italiano."""

    client = _get_client()

    try:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        testo = risposta.content[0].text
    except Exception:
        primo_kp = key_points[0] if key_points else "Come immaginate questo scenario?"
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
        aggiorna_scenario(scenario_gruppo["id"], narrativa="Nessun contributo individuale trovato per questo gruppo.", step_corrente="concluso")
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
  "narrativa": "Due o tre paragrafi che descrivono coerentemente il mondo futuro integrando le visioni. Includi una breve sezione che evidenzia esplicitamente 'Punti in Comune' e 'Divergenze Emerse' tra i vari partecipanti.",
  "minacce": ["minaccia unificata 1", "minaccia 2", "ecc"],
  "opportunita": ["opportunità unificata 1", "opportunità 2", "ecc"]
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
            step_corrente="concluso"
        )
    except Exception as e:
        aggiorna_scenario(
            scenario_gruppo["id"],
            narrativa=f"Errore durante la generazione della sintesi: {str(e)}",
            step_corrente="concluso"
        )

