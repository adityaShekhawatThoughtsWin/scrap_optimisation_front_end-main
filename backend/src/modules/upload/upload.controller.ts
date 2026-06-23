import { Request, Response } from "express";
import { UploadService } from "./upload.service";

const uploadService = new UploadService();

export class UploadController {
  uploadHeatQueryAll = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const { pairedId } = req.body;
    const record = await uploadService.saveHeatQueryAll(req.file!.path, pairedId ? Number(pairedId) : undefined);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };

  uploadGradeList = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const record = await uploadService.saveGradeList(req.file!.path);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };

  uploadScrapDataInventory = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const record = await uploadService.saveScrapDataInventory(req.file!.path);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };

  uploadHeatQuerySchedule = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const record = await uploadService.saveHeatQuerySchedule(req.file!.path);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };

  uploadScrapChem = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const record = await uploadService.saveScrapChem(req.file!.path);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };

  uploadHeatChem = async (
    req: Request & { file?: Express.Multer.File },
    res: Response
  ) => {
    const { pairedId } = req.body;
    const record = await uploadService.saveHeatChem(req.file!.path, pairedId ? Number(pairedId) : undefined);
    return res.status(200).json({ message: "File uploaded successfully", data: record });
  };
}