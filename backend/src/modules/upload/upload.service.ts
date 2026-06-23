import multer from "multer";
import path from "path";
import fs from "fs";
import { FileType } from "../../constants/types";
import { UploadRepository } from "./upload.repository";
import { sendToModel } from "../../lib/kalamClient";
import { cleanupOldFiles } from "../../lib/cleanup";
import { AppError } from "../../errors/AppError";

const uploadRepository = new UploadRepository();

const dest = path.join("uploaded_files");
if (!fs.existsSync(dest)) {
  fs.mkdirSync(dest, { recursive: true });
}

export const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, dest),
    filename: (_req, file, cb) => {
      const unique = `${Date.now()}-${file.originalname}`;
      cb(null, unique);
    },
  }),
});

export class UploadService {
  saveHeatQueryAll = async (filepath: string, pairedId?: number) => {
    cleanupOldFiles().catch(console.error);
    const record = await uploadRepository.createUploadRecord(filepath, FileType.heat_query_all);

    if (pairedId) {
      const paired = await uploadRepository.getById(pairedId);
      if (!paired) throw new AppError("Paired file record not found", 404);
      const modelResult=await sendToModel(record.filepath, paired.filepath);
      return { ...record, modelResult };
    }

    return record;
  };

  saveGradeList = async (filepath: string) => {
    return await uploadRepository.createUploadRecord(filepath, FileType.grade_list);
  };

  saveScrapDataInventory = async (filepath: string) => {
    return await uploadRepository.createUploadRecord(filepath, FileType.scrap_data_inventory);
  };

  saveHeatQuerySchedule = async (filepath: string) => {
    return await uploadRepository.createUploadRecord(filepath, FileType.heat_query_schedule);
  };

  saveScrapChem = async (filepath: string) => {
    return await uploadRepository.createUploadRecord(filepath, FileType.scrap_chem);
  };

  saveHeatChem = async (filepath: string, pairedId?: number) => {
    cleanupOldFiles().catch(console.error);
    const record = await uploadRepository.createUploadRecord(filepath, FileType.heat_chem);

    if (pairedId) {
      const paired = await uploadRepository.getById(pairedId);
      if (!paired) throw new AppError("Paired file record not found", 404);
      const modelResult = await sendToModel(paired.filepath, record.filepath);
      return { ...record, modelResult };
    }

    return record;
  };
}