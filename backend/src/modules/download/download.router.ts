import { Router } from "express";
import { DownloadController } from "./download.controller";
import { ROUTES } from "../../constants/route";
import { asyncHandler } from "../../middleware/asyncHandler";

const DownloadRouter = Router();
const controller = new DownloadController();

DownloadRouter.get(ROUTES.DOWNLOAD_HEAT_QUERY_ALL, asyncHandler(controller.downloadHeatQueryAll));
DownloadRouter.get(ROUTES.DOWNLOAD_GRADE_LIST, asyncHandler(controller.downloadGradeList));
DownloadRouter.get(ROUTES.DOWNLOAD_SCRAP_DATA_INVENTORY, asyncHandler(controller.downloadScrapDataInventory));
DownloadRouter.get(ROUTES.DOWNLOAD_HEAT_QUERY_SCHEDULE, asyncHandler(controller.downloadHeatQuerySchedule));
DownloadRouter.get(ROUTES.DOWNLOAD_SCRAP_CHEM, asyncHandler(controller.downloadScrapChem));
DownloadRouter.get(ROUTES.DOWNLOAD_HEAT_CHEM, asyncHandler(controller.downloadHeatChem));

export default DownloadRouter;