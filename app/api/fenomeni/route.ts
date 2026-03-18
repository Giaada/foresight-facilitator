import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// POST /api/fenomeni — aggiunge un fenomeno (facilitatore o partecipante)
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { testo, descrizione, sessioneId, codicePartecipante, codiceFacilitatore } = body;

  if (!testo || !sessioneId) {
    return NextResponse.json(
      { errore: "testo e sessioneId sono obbligatori" },
      { status: 400 }
    );
  }

  // Verifica che chi aggiunge appartenga alla sessione
  let autore = "facilitatore";
  let approvato = true;

  if (codicePartecipante) {
    const partecipante = await prisma.partecipante.findUnique({
      where: { codice: codicePartecipante },
    });
    if (!partecipante || partecipante.sessioneId !== sessioneId) {
      return NextResponse.json({ errore: "partecipante non valido" }, { status: 403 });
    }
    autore = partecipante.nome;
    approvato = false; // I fenomeni dei partecipanti vanno approvati
  } else if (codiceFacilitatore) {
    const sessione = await prisma.sessione.findUnique({
      where: { codiceFacilitatore },
    });
    if (!sessione || sessione.id !== sessioneId) {
      return NextResponse.json({ errore: "non autorizzato" }, { status: 403 });
    }
  } else {
    return NextResponse.json({ errore: "autenticazione mancante" }, { status: 401 });
  }

  const fenomeno = await prisma.fenomeno.create({
    data: { testo, descrizione: descrizione || null, autore, approvato, sessioneId },
  });

  return NextResponse.json(fenomeno);
}

// PATCH /api/fenomeni — approva/rifiuta un fenomeno (solo facilitatore)
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { fenomenoId, approvato, codiceFacilitatore } = body;

  const sessione = await prisma.sessione.findUnique({
    where: { codiceFacilitatore },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "non autorizzato" }, { status: 403 });
  }

  const fenomeno = await prisma.fenomeno.update({
    where: { id: fenomenoId },
    data: { approvato },
  });

  return NextResponse.json(fenomeno);
}
