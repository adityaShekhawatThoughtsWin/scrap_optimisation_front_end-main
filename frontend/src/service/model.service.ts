import { api } from "../api/axios";
import { API_ENDPOINT } from "../constants";
import type { PlannerFileIds } from "../utils/FileRead";

const modelService = {
    runModel: async (plannerFileIds: PlannerFileIds) => {
        const response = await api.post(API_ENDPOINT.MODEL_RUN, {
            scrapChemId: plannerFileIds.scrapChemId!,
            heatQueryScheduleId: plannerFileIds.heatQueryScheduleId!,
            scrapInventoryId: plannerFileIds.scrapInventoryId!,
            gradeFileId: plannerFileIds.gradeListId!,
        });
        return response.data;
    }
}

export default modelService;