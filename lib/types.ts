export type StatoSessione =
  | "setup"
  | "horizon_scanning"
  | "transizione"
  | "scenario_planning"
  | "concluso";

export type StepScenario =
  | "intro"
  | "key_points"
  | "narrativa"
  | "titolo"
  | "minacce"
  | "opportunita"
  | "concluso";

export type RuoloMessaggio = "assistant" | "user";

export interface SessioneInfo {
  id: string;
  codice: string;
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
}

export interface FenomenoInfo {
  id: string;
  testo: string;
  descrizione?: string | null;
  autore: string;
  approvato: boolean;
}

export interface PartecipanteInfo {
  id: string;
  nome: string;
  codice: string;
  votato: boolean;
  gruppoId?: string | null;
}

export interface GruppoInfo {
  id: string;
  numero: number;
  quadrante: string;
  nomeScenario?: string | null;
  stepCorrente: StepScenario;
  partecipanti: PartecipanteInfo[];
}

export interface MessaggioChatInfo {
  id: string;
  autore: string;
  ruolo: RuoloMessaggio;
  contenuto: string;
  createdAt: string;
}

export interface ScenarioOutputInfo {
  narrativa?: string | null;
  titolo?: string | null;
  minacce?: string[] | null;
  opportunita?: string[] | null;
  keyPointsData?: Record<string, string> | null;
}

// Eventi WebSocket
export type SocketEvento =
  | { tipo: "stato_aggiornato"; stato: StatoSessione }
  | { tipo: "fenomeno_aggiunto"; fenomeno: FenomenoInfo }
  | { tipo: "fenomeno_approvato"; fenomenoId: string }
  | { tipo: "voto_completato"; partecipanteId: string }
  | { tipo: "messaggio_chat"; gruppoId: string; messaggio: MessaggioChatInfo }
  | { tipo: "step_aggiornato"; gruppoId: string; step: StepScenario }
  | { tipo: "scenario_aggiornato"; gruppoId: string; output: ScenarioOutputInfo };
