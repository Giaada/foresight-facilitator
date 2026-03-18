-- CreateTable
CREATE TABLE "Sessione" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "codice" TEXT NOT NULL,
    "codiceFacilitatore" TEXT NOT NULL,
    "domandaRicerca" TEXT NOT NULL,
    "frameTemporale" TEXT NOT NULL,
    "keyPoints" TEXT NOT NULL,
    "stato" TEXT NOT NULL DEFAULT 'setup',
    "driver1Nome" TEXT,
    "driver1PosPolo" TEXT,
    "driver1NegPolo" TEXT,
    "driver2Nome" TEXT,
    "driver2PosPolo" TEXT,
    "driver2NegPolo" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Fenomeno" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "testo" TEXT NOT NULL,
    "descrizione" TEXT,
    "autore" TEXT NOT NULL DEFAULT 'facilitatore',
    "approvato" BOOLEAN NOT NULL DEFAULT true,
    "sessioneId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Fenomeno_sessioneId_fkey" FOREIGN KEY ("sessioneId") REFERENCES "Sessione" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Partecipante" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "nome" TEXT NOT NULL,
    "codice" TEXT NOT NULL,
    "sessioneId" TEXT NOT NULL,
    "gruppoId" TEXT,
    "votato" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Partecipante_sessioneId_fkey" FOREIGN KEY ("sessioneId") REFERENCES "Sessione" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Partecipante_gruppoId_fkey" FOREIGN KEY ("gruppoId") REFERENCES "Gruppo" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Voto" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "posizione" INTEGER NOT NULL,
    "partecipanteId" TEXT NOT NULL,
    "fenomenoId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Voto_partecipanteId_fkey" FOREIGN KEY ("partecipanteId") REFERENCES "Partecipante" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Voto_fenomenoId_fkey" FOREIGN KEY ("fenomenoId") REFERENCES "Fenomeno" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Gruppo" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "numero" INTEGER NOT NULL,
    "quadrante" TEXT NOT NULL,
    "nomeScenario" TEXT,
    "sessioneId" TEXT NOT NULL,
    "stepCorrente" TEXT NOT NULL DEFAULT 'intro',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Gruppo_sessioneId_fkey" FOREIGN KEY ("sessioneId") REFERENCES "Sessione" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "MessaggioChat" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "autore" TEXT NOT NULL,
    "ruolo" TEXT NOT NULL,
    "contenuto" TEXT NOT NULL,
    "gruppoId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "MessaggioChat_gruppoId_fkey" FOREIGN KEY ("gruppoId") REFERENCES "Gruppo" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "ScenarioOutput" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "gruppoId" TEXT NOT NULL,
    "narrativa" TEXT,
    "titolo" TEXT,
    "minacce" TEXT,
    "opportunita" TEXT,
    "keyPointsData" TEXT,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "ScenarioOutput_gruppoId_fkey" FOREIGN KEY ("gruppoId") REFERENCES "Gruppo" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "Sessione_codice_key" ON "Sessione"("codice");

-- CreateIndex
CREATE UNIQUE INDEX "Sessione_codiceFacilitatore_key" ON "Sessione"("codiceFacilitatore");

-- CreateIndex
CREATE UNIQUE INDEX "Partecipante_codice_key" ON "Partecipante"("codice");

-- CreateIndex
CREATE UNIQUE INDEX "Voto_partecipanteId_fenomenoId_key" ON "Voto"("partecipanteId", "fenomenoId");

-- CreateIndex
CREATE UNIQUE INDEX "ScenarioOutput_gruppoId_key" ON "ScenarioOutput"("gruppoId");
