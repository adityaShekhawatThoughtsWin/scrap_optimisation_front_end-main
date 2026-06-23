import { Router } from "express";
import { UploadController } from "./upload.controller";
import { upload } from "./upload.service";
import { ROUTES } from "../../constants/route";
import { asyncHandler } from "../../middleware/asyncHandler";

const UploadRouter = Router();
const controller = new UploadController();

UploadRouter.use(upload.single("file"));

UploadRouter.post(ROUTES.UPLOAD_HEAT_QUERY_ALL, asyncHandler(controller.uploadHeatQueryAll));
UploadRouter.post(ROUTES.UPLOAD_GRADE_LIST, asyncHandler(controller.uploadGradeList));
UploadRouter.post(ROUTES.UPLOAD_SCRAP_DATA_INVENTORY, asyncHandler(controller.uploadScrapDataInventory));
UploadRouter.post(ROUTES.UPLOAD_HEAT_QUERY_SCHEDULE, asyncHandler(controller.uploadHeatQuerySchedule));
UploadRouter.post(ROUTES.UPLOAD_SCRAP_CHEM, asyncHandler(controller.uploadScrapChem));
UploadRouter.post(ROUTES.UPLOAD_HEAT_CHEM, asyncHandler(controller.uploadHeatChem));

export default UploadRouter;