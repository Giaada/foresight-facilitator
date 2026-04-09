"use client";
import { Clock, Search } from "lucide-react";
import { StatoSessione } from "@/lib/types";

const LABEL_STATO: Record<StatoSessione, string> = {
  setup: "Setup",
  horizon_scanning: "Horizon Scanning",
  transizione: "Transizione",
  scenario_planning_individuale: "Scenario — Individuale",
  scenario_planning_gruppo: "Scenario — Gruppo",
  concluso: "Concluso",
};

const COLORE_STATO: Record<StatoSessione, string> = {
  setup: "bg-gray-100 text-gray-700",
  horizon_scanning: "bg-blue-100 text-blue-800",
  transizione: "bg-yellow-100 text-yellow-800",
  scenario_planning_individuale: "bg-violet-100 text-violet-800",
  scenario_planning_gruppo: "bg-indigo-100 text-indigo-800",
  concluso: "bg-green-100 text-green-800",
};

interface HeaderSessioneProps {
  domandaRicerca: string;
  frameTemporale: string;
  stato: StatoSessione;
  ruolo?: "facilitatore" | "partecipante";
}

export function HeaderSessione({
  domandaRicerca,
  frameTemporale,
  stato,
  ruolo = "partecipante",
}: HeaderSessioneProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-start justify-between gap-4 flex-wrap">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Search size={14} className="text-gray-400 shrink-0" />
            <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">
              Domanda di ricerca
            </span>
          </div>
          <p className="text-gray-900 font-medium leading-snug">{domandaRicerca}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <Clock size={14} className="text-gray-400" />
            <span className="font-medium">{frameTemporale}</span>
          </div>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${COLORE_STATO[stato]}`}
          >
            {LABEL_STATO[stato]}
          </span>
          {ruolo === "facilitatore" && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
              Facilitatore
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
