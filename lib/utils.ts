import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function generaCodice(lunghezza = 6): string {
  const caratteri = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let codice = "";
  for (let i = 0; i < lunghezza; i++) {
    codice += caratteri.charAt(Math.floor(Math.random() * caratteri.length));
  }
  return codice;
}

export function calcolaRankingAggregato(
  voti: Array<{ fenomenoId: string; posizione: number }>
): Array<{ fenomenoId: string; mediaPostazione: number; conteggio: number }> {
  const mappa: Record<string, { somma: number; conteggio: number }> = {};

  for (const voto of voti) {
    if (!mappa[voto.fenomenoId]) {
      mappa[voto.fenomenoId] = { somma: 0, conteggio: 0 };
    }
    mappa[voto.fenomenoId].somma += voto.posizione;
    mappa[voto.fenomenoId].conteggio += 1;
  }

  return Object.entries(mappa)
    .map(([fenomenoId, { somma, conteggio }]) => ({
      fenomenoId,
      mediaPostazione: somma / conteggio,
      conteggio,
    }))
    .sort((a, b) => a.mediaPostazione - b.mediaPostazione);
}
