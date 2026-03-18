import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { generaCodice } from "@/lib/utils";

// POST /api/partecipanti — registra un partecipante alla sessione
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { nome, codiceSessione } = body;

  if (!nome || !codiceSessione) {
    return NextResponse.json(
      { errore: "nome e codiceSessione sono obbligatori" },
      { status: 400 }
    );
  }

  const sessione = await prisma.sessione.findUnique({
    where: { codice: codiceSessione },
  });

  if (!sessione) {
    return NextResponse.json({ errore: "sessione non trovata" }, { status: 404 });
  }

  if (sessione.stato !== "horizon_scanning") {
    return NextResponse.json(
      { errore: "la sessione non è in fase di horizon scanning" },
      { status: 400 }
    );
  }

  const codice = generaCodice(6);

  const partecipante = await prisma.partecipante.create({
    data: {
      nome,
      codice,
      sessioneId: sessione.id,
    },
  });

  return NextResponse.json({
    id: partecipante.id,
    nome: partecipante.nome,
    codice: partecipante.codice,
    sessioneId: partecipante.sessioneId,
  });
}
