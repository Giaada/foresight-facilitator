-- CreateTable
CREATE TABLE "ScenarioIndividuale" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "partecipanteId" TEXT NOT NULL,
    "sessioneId" TEXT NOT NULL,
    "quadrante" TEXT NOT NULL,
    "stepCorrente" TEXT NOT NULL DEFAULT 'intro',
    "narrativa" TEXT,
    "titolo" TEXT,
    "minacce" TEXT,
    "opportunita" TEXT,
    "keyPointsData" TEXT,
    "concluso" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "ScenarioIndividuale_partecipanteId_fkey" FOREIGN KEY ("partecipanteId") REFERENCES "Partecipante" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "ScenarioIndividuale_sessioneId_fkey" FOREIGN KEY ("sessioneId") REFERENCES "Sessione" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "MessaggioChatIndividuale" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "autore" TEXT NOT NULL,
    "ruolo" TEXT NOT NULL,
    "contenuto" TEXT NOT NULL,
    "scenarioIndividualeId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "MessaggioChatIndividuale_scenarioIndividualeId_fkey" FOREIGN KEY ("scenarioIndividualeId") REFERENCES "ScenarioIndividuale" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "ScenarioIndividuale_partecipanteId_key" ON "ScenarioIndividuale"("partecipanteId");
