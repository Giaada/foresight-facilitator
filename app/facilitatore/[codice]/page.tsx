"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { io, Socket } from "socket.io-client";
import { HeaderSessione } from "@/components/shared/HeaderSessione";
import { VistaPannelloSetup } from "@/components/facilitatore/VistaPannelloSetup";
import { VistaHorizonScanning } from "@/components/facilitatore/VistaHorizonScanning";
import { VistaTransizione } from "@/components/facilitatore/VistaTransizione";
import { VistaScenarioPlanning } from "@/components/facilitatore/VistaScenarioPlanning";
import type { StatoSessione } from "@/lib/types";

interface DatiSessione {
  id: string;
  codice: string;
  codiceFacilitatore: string;
  domandaRicerca: string;
  frameTemporale: string;
  keyPoints: string[];
  stato: StatoSessione;
  driver1Nome?: string | null;
  driver1PosPolo?: string | null;
  driver1NegPolo?: string | null;
  driver2Nome?: string | null;
  driver2PosPolo?: string | null;
  driver2NegPolo?: string | null;
  fenomeni: Fenomeno[];
  partecipanti: Partecipante[];
  gruppi: Gruppo[];
  rankingAggregato: { fenomenoId: string; mediaPostazione: number; conteggio: number }[];
}

interface Fenomeno {
  id: string;
  testo: string;
  descrizione?: string | null;
  autore: string;
  approvato: boolean;
}

interface Partecipante {
  id: string;
  nome: string;
  codice: string;
  votato: boolean;
  gruppoId?: string | null;
}

interface Gruppo {
  id: string;
  numero: number;
  quadrante: string;
  nomeScenario?: string | null;
  stepCorrente: string;
  partecipanti: Partecipante[];
  scenarioOutput?: {
    narrativa?: string | null;
    titolo?: string | null;
    minacce?: string[];
    opportunita?: string[];
  } | null;
}

export default function DashboardFacilitatore() {
  const { codice } = useParams<{ codice: string }>();
  const [dati, setDati] = useState<DatiSessione | null>(null);
  const [errore, setErrore] = useState("");
  const [socket, setSocket] = useState<Socket | null>(null);

  const caricaDati = useCallback(async () => {
    const res = await fetch(`/api/sessione/facilitatore?codice=${codice}`);
    if (!res.ok) { setErrore("Sessione non trovata."); return; }
    const json = await res.json();
    setDati(json);
  }, [codice]);

  useEffect(() => {
    caricaDati();
  }, [caricaDati]);

  useEffect(() => {
    if (!dati) return;
    const s = io({ path: "/socket.io" });
    setSocket(s);

    s.emit("entra_sessione", { sessioneId: dati.id, ruolo: "facilitatore" });

    s.on("voto_completato", ({ partecipanteId }: { partecipanteId: string }) => {
      setDati((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          partecipanti: prev.partecipanti.map((p) =>
            p.id === partecipanteId ? { ...p, votato: true } : p
          ),
        };
      });
    });

    s.on("fenomeno_aggiunto", ({ fenomeno }: { fenomeno: Fenomeno }) => {
      setDati((prev) => {
        if (!prev) return prev;
        return { ...prev, fenomeni: [...prev.fenomeni, fenomeno] };
      });
    });

    s.on("gruppo_aggiornato", ({ gruppoId, step }: { gruppoId: string; step: string }) => {
      setDati((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          gruppi: prev.gruppi.map((g) =>
            g.id === gruppoId ? { ...g, stepCorrente: step } : g
          ),
        };
      });
    });

    s.on("stato_aggiornato", ({ stato }: { stato: StatoSessione }) => {
      setDati((prev) => prev ? { ...prev, stato } : prev);
      caricaDati();
    });

    return () => { s.disconnect(); };
  }, [dati?.id, caricaDati]);

  async function cambiaStato(nuovoStato: StatoSessione) {
    await fetch("/api/sessione/facilitatore", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codice, stato: nuovoStato }),
    });
    socket?.emit("stato_aggiornato", { sessioneId: dati?.id, stato: nuovoStato });
    caricaDati();
  }

  async function approvaFenomeno(fenomenoId: string, approvato: boolean) {
    await fetch("/api/fenomeni", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fenomenoId, approvato, codiceFacilitatore: codice }),
    });
    setDati((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        fenomeni: prev.fenomeni.map((f) =>
          f.id === fenomenoId ? { ...f, approvato } : f
        ),
      };
    });
    socket?.emit("fenomeno_approvato", { sessioneId: dati?.id, fenomenoId });
  }

  async function aggiungiFenomeno(testo: string, descrizione?: string) {
    const res = await fetch("/api/fenomeni", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        testo,
        descrizione,
        sessioneId: dati?.id,
        codiceFacilitatore: codice,
      }),
    });
    const fenomeno = await res.json();
    setDati((prev) => prev ? { ...prev, fenomeni: [...prev.fenomeni, fenomeno] } : prev);
    socket?.emit("fenomeno_aggiunto", { sessioneId: dati?.id, fenomeno });
  }

  if (errore) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-600">{errore}</p>
      </div>
    );
  }

  if (!dati) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <HeaderSessione
        domandaRicerca={dati.domandaRicerca}
        frameTemporale={dati.frameTemporale}
        stato={dati.stato}
        ruolo="facilitatore"
      />

      {/* Banner codice sessione */}
      <div className="bg-indigo-700 text-white px-6 py-2">
        <div className="max-w-5xl mx-auto flex items-center justify-between text-sm">
          <span>
            Codice sessione partecipanti:{" "}
            <span className="font-mono font-bold text-lg tracking-widest">{dati.codice}</span>
          </span>
          <span className="text-indigo-200">
            {dati.partecipanti.filter((p) => p.votato).length}/{dati.partecipanti.length} hanno votato
          </span>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {dati.stato === "setup" && (
          <VistaPannelloSetup
            dati={dati}
            onAvviaHorizonScanning={() => cambiaStato("horizon_scanning")}
            onAggiungiFenomeno={aggiungiFenomeno}
          />
        )}

        {dati.stato === "horizon_scanning" && (
          <VistaHorizonScanning
            dati={dati}
            onApprovaFenomeno={approvaFenomeno}
            onAggiungiFenomeno={aggiungiFenomeno}
            onChiudiFase={() => cambiaStato("transizione")}
          />
        )}

        {dati.stato === "transizione" && (
          <VistaTransizione
            dati={dati}
            codiceFacilitatore={codice}
            onAvviaScenarioPlanning={() => cambiaStato("scenario_planning")}
            onAggiorna={caricaDati}
          />
        )}

        {(dati.stato === "scenario_planning" || dati.stato === "concluso") && (
          <VistaScenarioPlanning
            dati={dati}
            onChiudiSessione={() => cambiaStato("concluso")}
            onAggiorna={caricaDati}
          />
        )}
      </main>
    </div>
  );
}
