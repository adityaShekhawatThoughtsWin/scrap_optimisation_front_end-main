// src/constants/routes.ts

export const ROUTES = {
  API_ROOT: "/api/v1",
  API_HEALTH: "/health",

  MODEL_ROOT: "/model",
  MODEL_RUN: "/run_model",

  UPLOAD_ROOT: "/upload",
  UPLOAD_HEAT_QUERY_ALL: "/heat-query-all",
  UPLOAD_GRADE_LIST: "/grade-list",
  UPLOAD_SCRAP_DATA_INVENTORY: "/scrap-data-inventory",
  UPLOAD_HEAT_QUERY_SCHEDULE: "/heat-query-schedule",
  UPLOAD_SCRAP_CHEM: "/scrap-chem",
  UPLOAD_HEAT_CHEM: "/heat-chem",

  DOWNLOAD_ROOT: "/download",
  DOWNLOAD_HEAT_QUERY_ALL: "/heat-query-all",
  DOWNLOAD_GRADE_LIST: "/grade-list",
  DOWNLOAD_SCRAP_DATA_INVENTORY: "/scrap-data-inventory",
  DOWNLOAD_HEAT_QUERY_SCHEDULE: "/heat-query-schedule",
  DOWNLOAD_SCRAP_CHEM: "/scrap-chem",
  DOWNLOAD_HEAT_CHEM: "/heat-chem",
} as const;