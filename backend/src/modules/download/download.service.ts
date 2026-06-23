import fs from "fs";
import path from "path";
import { FileType } from "../../constants/types";
import { DownloadRepository } from "./download.repository";
import { AppError } from "../../errors/AppError";

const downloadRepository = new DownloadRepository();

const getMimeType = (filepath: string) => {
  const ext = path.extname(filepath).toLowerCase();
  switch (ext) {
    case ".csv":  return "text/csv";
    case ".xlsx": return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    case ".pdf":  return "application/pdf";
    case ".json": return "application/json";
    case ".txt":  return "text/plain";
    default:      return "application/octet-stream";
  }
};

const readAsBase64 = (filepath: string) => {
  const absPath = path.resolve(filepath);
  if (!fs.existsSync(absPath)) throw new AppError("File not found on disk", 404);
  const buffer = fs.readFileSync(absPath);
  return {
    filename: path.basename(absPath).replace(/^\d+-/, ""),
    mimeType: getMimeType(absPath),
    size: buffer.length,
    data: buffer.toString("base64"),
  };
};

export class DownloadService {
  getLatestHeatQueryAll = async () => {
    const record = await downloadRepository.getLatestByType(FileType.heat_query_all);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };

  getLatestGradeList = async () => {
    const record = await downloadRepository.getLatestByType(FileType.grade_list);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };

  getLatestScrapDataInventory = async () => {
    const record = await downloadRepository.getLatestByType(FileType.scrap_data_inventory);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };

  getLatestHeatQuerySchedule = async () => {
    const record = await downloadRepository.getLatestByType(FileType.heat_query_schedule);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };

  getLatestScrapChem = async () => {
    const record = await downloadRepository.getLatestByType(FileType.scrap_chem);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };

  getLatestHeatChem = async () => {
    const record = await downloadRepository.getLatestByType(FileType.heat_chem);
    if (!record) return null;
    return readAsBase64(record.filepath);
  };
}