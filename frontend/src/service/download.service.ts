import { api } from "../api/axios";
import { API_ENDPOINT } from "../constants";

const downloadService = {
    downloadHeatQueryAll: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_HEAT_QUERY_ALL);
        return response.data;
    },
    downloadGradeList: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_GRADE_LIST);
        return response.data;
    },
    downloadScrapDataInventory: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_SCRAP_DATA_INVENTORY);
        return response.data;
    },
    downloadHeatQuerySchedule: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_HEAT_QUERY_SCHEDULE);
        return response.data;
    },
    downloadScrapChem: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_SCRAP_CHEM);
        return response.data;
    },
    downloadHeatChem: async () => {
        const response = await api.get(API_ENDPOINT.DOWNLOAD_HEAT_CHEM);
        return response.data;
    }
}
export default downloadService;