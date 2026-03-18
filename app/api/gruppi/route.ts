import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// POST /api/gruppi — crea i 4 gruppi (solo facilitatore)
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { codiceFacilitatore, gruppi } = body;
  // gruppi: Array<{ numero: number; quadrante: string; partecipantiIds: string[] }>

  const sessione = await prisma.sessione.findUnique({
    where: { codiceFacilitatore },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "non autorizzato" }, { status: 403 });
  }

  // Elimina gruppi esistenti
  await prisma.gruppo.deleteMany({ where: { sessioneId: sessione.id } });

  const gruppiCreati = await Promise.all(
    gruppi.map(
      async (g: { numero: number; quadrante: string; partecipantiIds: string[] }) => {
        const gruppo = await prisma.gruppo.create({
          data: {
            numero: g.numero,
            quadrante: g.quadrante,
            sessioneId: sessione.id,
          },
        });

        await prisma.partecipante.updateMany({
          where: { id: { in: g.partecipantiIds } },
          data: { gruppoId: gruppo.id },
        });

        return gruppo;
      }
    )
  );

  return NextResponse.json(gruppiCreati);
}

// GET /api/gruppi?codicePartecipante=XXX — recupera il gruppo di un partecipante
export async function GET(req: NextRequest) {
  const codicePartecipante = req.nextUrl.searchParams.get("codicePartecipante");

  if (!codicePartecipante) {
    return NextResponse.json({ errore: "codicePartecipante obbligatorio" }, { status: 400 });
  }

  const partecipante = await prisma.partecipante.findUnique({
    where: { codice: codicePartecipante },
    include: {
      gruppo: {
        include: {
          partecipanti: true,
          messaggi: { orderBy: { createdAt: "asc" } },
          scenarioOutput: true,
        },
      },
      sessione: true,
    },
  });

  if (!partecipante || !partecipante.gruppo) {
    return NextResponse.json({ errore: "gruppo non trovato" }, { status: 404 });
  }

  const { gruppo, sessione } = partecipante;

  return NextResponse.json({
    gruppo: {
      id: gruppo.id,
      numero: gruppo.numero,
      quadrante: gruppo.quadrante,
      nomeScenario: gruppo.nomeScenario,
      stepCorrente: gruppo.stepCorrente,
      partecipanti: gruppo.partecipanti,
      messaggi: gruppo.messaggi,
      scenarioOutput: gruppo.scenarioOutput
        ? {
            narrativa: gruppo.scenarioOutput.narrativa,
            titolo: gruppo.scenarioOutput.titolo,
            minacce: gruppo.scenarioOutput.minacce
              ? JSON.parse(gruppo.scenarioOutput.minacce)
              : [],
            opportunita: gruppo.scenarioOutput.opportunita
              ? JSON.parse(gruppo.scenarioOutput.opportunita)
              : [],
            keyPointsData: gruppo.scenarioOutput.keyPointsData
              ? JSON.parse(gruppo.scenarioOutput.keyPointsData)
              : {},
          }
        : null,
    },
    sessione: {
      domandaRicerca: sessione.domandaRicerca,
      frameTemporale: sessione.frameTemporale,
      keyPoints: JSON.parse(sessione.keyPoints),
      driver1Nome: sessione.driver1Nome,
      driver1PosPolo: sessione.driver1PosPolo,
      driver1NegPolo: sessione.driver1NegPolo,
      driver2Nome: sessione.driver2Nome,
      driver2PosPolo: sessione.driver2PosPolo,
      driver2NegPolo: sessione.driver2NegPolo,
    },
  });
}
