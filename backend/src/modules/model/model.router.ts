import { Router } from "express";
import { ModelController } from "./model.controller";
import { ROUTES } from "../../constants/route";
import { asyncHandler } from "../../middleware/asyncHandler";

const ModelRouter = Router();
const controller = new ModelController();

ModelRouter.post(ROUTES.MODEL_RUN, asyncHandler(controller.modelRun));

export default ModelRouter;