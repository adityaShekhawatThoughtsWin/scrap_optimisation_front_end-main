import { formDataApi } from '../api/axios';
import { API_ENDPOINT } from '../constants';

const uploadService = {
  uploadHeatQueryAll: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.HEAT_QUERY_ALL, formData);
    return response.data;
  },
  uploadHeatChem: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.HEAT_CHEM, formData);
    return response.data;
  },
  uploadGradeList: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.GRADE_LIST, formData);
    return response.data;
  },
  uploadScrapDataInventory: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.SCRAP_DATA_INVENTORY, formData);
    return response.data;
  },
  uploadHeatQuerySchedule: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.HEAT_QUERY_SCHEDULE, formData);
    return response.data;
  },
  uploadScrapChem: async (formData: FormData) => {
    const response = await formDataApi.post(API_ENDPOINT.SCRAP_CHEM, formData);
    return response.data;
  },
}

export default uploadService;