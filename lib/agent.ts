import Anthropic from "@anthropic-ai/sdk";
import { prisma } from "./prisma";
import { StepScenario } from "./types";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface RispostaAgente {
  testo: string;
  nuovoStep?: StepScenario;
  outputAggiornato?: {
    narrativa?: string;
    titolo?: string;
    minacce?: string[];
    opportunita?: string[];
    keyPointsData?: Record<string, string>;
  };
}

export async function eseguiStepAgente(
  gruppoId: string,
  ultimoMessaggioUtente: string
): Promise<RispostaAgente | null> {
  const gruppo = await prisma.gruppo.findUnique({
    where: { id: gruppoId },
    include: {
      sessione: true,
      messaggi: { orderBy: { createdAt: "asc" } },
      scenarioOutput: true,
    },
  });

  if (!gruppo) return null;

  const sessione = gruppo.sessione;
  const keyPoints: string[] = JSON.parse(sessione.keyPoints);
  const stepCorrente = gruppo.stepCorrente as StepScenario;

  // Costruisce la descrizione del quadrante
  const descrizioneQuadrante = costruisciDescrizioneQuadrante(
    gruppo.quadrante,
    sessione.driver1Nome,
    sessione.driver1PosPolo,
    sessione.driver1NegPolo,
    sessione.driver2Nome,
    sessione.driver2PosPolo,
    sessione.driver2NegPolo
  );

  const sistemaPrompt = `Sei un facilitatore esperto di Strategic Foresight.
Stai guidando un piccolo gruppo (4 persone) nella costruzione di uno scenario futuro.

CONTESTO DELLA SESSIONE:
- Domanda di ricerca: "${sessione.domandaRicerca}"
- Orizzonte temporale: ${sessione.frameTemporale}
- Il vostro quadrante: ${descrizioneQuadrante}

STEP CORRENTE: ${stepCorrente}
KEY POINTS da esplorare: ${keyPoints.join(", ")}

ISTRUZIONI DI COMPORTAMENTO:
- Comunica in italiano, con tono professionale ma accessibile
- Fai UNA domanda alla volta, non sovraccaricare il gruppo
- Sii specifico e concreto, ancorato all'orizzonte temporale
- Valida e integra le risposte del gruppo prima di andare avanti
- Quando hai abbastanza materiale per uno step, avanza al successivo

FORMATO RISPOSTA:
Rispondi SEMPRE con un JSON in questo formato:
{
  "testo": "il messaggio da mostrare al gruppo",
  "nuovoStep": "solo se stai avanzando di step, altrimenti null",
  "outputAggiornato": {
    "narrativa": "testo della narrativa in elaborazione",
    "titolo": "titolo (se definito)",
    "minacce": ["eventuali", "minacce", "emerse"],
    "opportunita": ["eventuali", "opportunità", "emerse"],
    "keyPointsData": {"nome_keypoint": "risposta_consolidata"}
  }
}
IMPORTANTE: Compila sempre in 'outputAggiornato' tutti i campi che stai via via definendo con il gruppo. Aggiorna questi campi non appena emergono spunti utili dalle risposte del gruppo, in modo che il report visivo si aggiorni in tempo reale lungo tutta la sessione. Se un campo non è ancora stato affrontato, può essere omesso o lasciato a null.`;

  // Costruisce la history dei messaggi
  const history = gruppo.messaggi.map((m: { ruolo: string; contenuto: string }) => ({
    role: m.ruolo as "user" | "assistant",
    content: m.contenuto,
  }));

  // Se è il primo messaggio (intro), aggiungi il trigger iniziale
  if (stepCorrente === "intro" && history.length === 0) {
    return await generaIntroduzione(gruppo.numero, descrizioneQuadrante, sessione.domandaRicerca, sessione.frameTemporale);
  }

  try {
    const risposta = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      system: sistemaPrompt,
      messages: [
        ...history,
        { role: "user", content: ultimoMessaggioUtente },
      ],
    });

    const testoRisposta = risposta.content[0].type === "text" ? risposta.content[0].text : "";

    // Prova a parsare il JSON dalla risposta
    try {
      const jsonMatch = testoRisposta.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          testo: parsed.testo || testoRisposta,
          nuovoStep: parsed.nuovoStep || undefined,
          outputAggiornato: parsed.outputAggiornato || undefined,
        };
      }
    } catch {
      // Se il parse fallisce, restituisce solo il testo
    }

    return { testo: testoRisposta };
  } catch (err) {
    console.error("[Agente] errore Anthropic:", err);
    return null;
  }
}

async function generaIntroduzione(
  numeroGruppo: number,
  descrizioneQuadrante: string,
  domandaRicerca: string,
  frameTemporale: string
): Promise<RispostaAgente> {
  try {
    const risposta = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: `Genera un messaggio di benvenuto per il Gruppo ${numeroGruppo} che inizia a lavorare sul seguente scenario di Strategic Foresight.

Domanda di ricerca: "${domandaRicerca}"
Orizzonte temporale: ${frameTemporale}
Quadrante assegnato: ${descrizioneQuadrante}

Il messaggio deve:
1. Presentare il quadrante in modo chiaro e stimolante
2. Spiegare brevemente cosa faranno (costruire lo scenario paso a paso)
3. Invitarli a rispondere "pronti" o fare domande prima di iniziare

Rispondi SOLO con il testo del messaggio, in italiano, tono coinvolgente.`,
        },
      ],
    });

    const testo =
      risposta.content[0].type === "text" ? risposta.content[0].text : "Benvenuti! Siete pronti a iniziare?";

    return { testo, nuovoStep: "intro" };
  } catch {
    return {
      testo: `Benvenuti Gruppo ${numeroGruppo}! Lavorerete sullo scenario: **${descrizioneQuadrante}**.\n\nQuando siete pronti, dite "pronti" e inizieremo insieme la costruzione dello scenario.`,
      nuovoStep: "intro",
    };
  }
}

function costruisciDescrizioneQuadrante(
  quadrante: string,
  d1Nome: string | null,
  d1Pos: string | null,
  d1Neg: string | null,
  d2Nome: string | null,
  d2Pos: string | null,
  d2Neg: string | null
): string {
  if (!d1Nome || !d2Nome) return `Quadrante ${quadrante}`;

  const asseX = quadrante[0] === "+" ? d1Pos || `${d1Nome} alto` : d1Neg || `${d1Nome} basso`;
  const asseY = quadrante[1] === "+" ? d2Pos || `${d2Nome} alto` : d2Neg || `${d2Nome} basso`;

  return `${asseX} × ${asseY} (Driver: ${d1Nome} e ${d2Nome})`;
}
