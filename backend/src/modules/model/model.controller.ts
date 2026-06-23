import { Request, Response } from "express";
import { ModelService } from "./model.service";

const modelService = new ModelService();

export class ModelController {
  modelRun = async (req: Request, res: Response) => {
    const { scrapChemId, heatQueryScheduleId, scrapInventoryId, gradeFileId } = req.body;
    const result = await modelService.runModel(
      Number(scrapChemId),
      Number(heatQueryScheduleId),
      Number(scrapInventoryId),
      gradeFileId ? Number(gradeFileId) : undefined
    );
    return res.status(200).json({ message: "Planner run successful", data: result });
  };
}