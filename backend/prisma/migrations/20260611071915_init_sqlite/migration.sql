-- CreateTable
CREATE TABLE "data" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "filepath" TEXT NOT NULL,
    "upload_type" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOLEAN NOT NULL DEFAULT false
);
