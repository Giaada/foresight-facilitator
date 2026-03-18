import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { generaCodice } from "@/lib/utils";

// POST /api/sessione — crea nuova sessione
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { domandaRicerca, frameTemporale, keyPoints, fenomeni } = body;

  if (!domandaRicerca || !frameTemporale) {
    return NextResponse.json(
      { errore: "domandaRicerca e frameTemporale sono obbligatori" },
      { status: 400 }
    );
  }

  const codice = generaCodice(6);
  const codiceFacilitatore = generaCodice(8);

  const sessione = await prisma.sessione.create({
    data: {
      codice,
      codiceFacilitatore,
      domandaRicerca,
      frameTemporale,
      keyPoints: JSON.stringify(keyPoints || []),
      fenomeni: {
        create: (fenomeni || []).map((f: { testo: string; descrizione?: string }) => ({
          testo: f.testo,
          descrizione: f.descrizione || null,
          autore: "facilitatore",
          approvato: true,
        })),
      },
    },
    include: { fenomeni: true },
  });

  return NextResponse.json({
    id: sessione.id,
    codice: sessione.codice,
    codiceFacilitatore: sessione.codiceFacilitatore,
  });
}

// GET /api/sessione?codice=XXX — recupera sessione per codice partecipante
export async function GET(req: NextRequest) {
  const codice = req.nextUrl.searchParams.get("codice");

  if (!codice) {
    return NextResponse.json({ errore: "codice obbligatorio" }, { status: 400 });
  }

  const sessione = await prisma.sessione.findUnique({
    where: { codice },
    include: {
      fenomeni: { where: { approvato: true }, orderBy: { createdAt: "asc" } },
    },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "sessione non trovata" }, { status: 404 });
  }

  return NextResponse.json({
    id: sessione.id,
    codice: sessione.codice,
    domandaRicerca: sessione.domandaRicerca,
    frameTemporale: sessione.frameTemporale,
    keyPoints: JSON.parse(sessione.keyPoints),
    stato: sessione.stato,
    fenomeni: sessione.fenomeni,
  });
}
