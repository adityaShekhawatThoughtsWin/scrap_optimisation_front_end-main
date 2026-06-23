import fs from "fs";
import { prisma } from "./prisma";
import { logger } from "./logger";

const isFirstUploadToday = async (): Promise<boolean> => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const count = await prisma.data.count({
    where: { created_at: { gte: today } },
  });
  logger.info({ count }, "isFirstUploadToday count");
  return count === 0;
};

const getPreviousWorkingDayStart = async (): Promise<Date | null> => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const lastRecord = await prisma.data.findFirst({
    where: { created_at: { lt: today }, is_deleted: false },
    orderBy: { created_at: "desc" },
    select: { created_at: true },
  });
  logger.info({ lastRecord }, "prevWorkingDayStart lastRecord");
  if (!lastRecord) return null;
  const prevDay = new Date(lastRecord.created_at);
  prevDay.setHours(0, 0, 0, 0);
  return prevDay;
};

const getOldRecords = async (before: Date) => {
  const records = await prisma.data.findMany({
    where: { created_at: { lt: before }, is_deleted: false },
    select: { id: true, filepath: true },
  });
  logger.info({ count: records.length }, "oldRecords count");
  return records;
};

const deleteFilesFromDisk = (filepaths: string[]): void => {
  for (const filepath of filepaths) {
    try {
      if (fs.existsSync(filepath)) {
        fs.unlinkSync(filepath);
      }
    } catch (err) {
      logger.error({ err, filepath }, "Failed to delete file");
    }
  }
};

const softDeleteRecordsInDb = async (ids: number[]): Promise<void> => {
  await prisma.data.updateMany({
    where: { id: { in: ids } },
    data: { is_deleted: true },
  });
};

export const cleanupOldFiles = async (): Promise<void> => {
  try {
    const firstUpload = await isFirstUploadToday();
    if (!firstUpload) return;

    const prevWorkingDayStart = await getPreviousWorkingDayStart();
    logger.info({ prevWorkingDayStart }, "prevWorkingDayStart");
    if (!prevWorkingDayStart) return;

    const oldRecords = await getOldRecords(prevWorkingDayStart);
    if (oldRecords.length === 0) return;

    deleteFilesFromDisk(oldRecords.map((r) => r.filepath));
    await softDeleteRecordsInDb(oldRecords.map((r) => r.id));
    logger.info({ deletedCount: oldRecords.length }, "Cleanup completed");
  } catch (err) {
    logger.error({err}, "Cleanup failed");
  }
};