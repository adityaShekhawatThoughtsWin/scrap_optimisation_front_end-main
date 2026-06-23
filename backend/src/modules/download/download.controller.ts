import { Request, Response } from "express";
import { DownloadService } from "./download.service";

const downloadService = new DownloadService();

export class DownloadController {
  downloadHeatQueryAll = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestHeatQueryAll();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };

  downloadGradeList = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestGradeList();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };

  downloadScrapDataInventory = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestScrapDataInventory();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };

  downloadHeatQuerySchedule = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestHeatQuerySchedule();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };

  downloadScrapChem = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestScrapChem();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };

  downloadHeatChem = async (_req: Request, res: Response) => {
    const record = await downloadService.getLatestHeatChem();
    if (!record) return res.status(404).json({ message: "No file found" });
    return res.json(record);
  };
}