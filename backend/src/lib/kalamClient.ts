import fs from "fs";
import path from "path";
import FormData from "form-data";
import axios from "axios";
import { config } from "../config";
import { AppError } from "../errors/AppError";

export const sendToModel = async (
  heatQueryAllPath: string,
  heatChemPath: string,
  targetChem: string = "ALL",
  returnFormat: string = "both"
) => {
  // step 1 - upload both files
  if (!fs.existsSync(heatQueryAllPath)) throw new AppError(`Heat Query All file not found: ${heatQueryAllPath}`, 404);

  if (!fs.existsSync(heatChemPath)) throw new AppError(`Heat Chem file not found: ${heatChemPath}`, 404);

  const formData = new FormData();
  formData.append("file1", fs.createReadStream(heatQueryAllPath), path.basename(heatQueryAllPath).replace(/^\d+-/, ""));
  formData.append("file2", fs.createReadStream(heatChemPath), path.basename(heatChemPath).replace(/^\d+-/, ""));

  const uploadRes = await axios.post(`${config.FLASK_BASE_URL}/upload`, formData, {
    headers: formData.getHeaders(),
  });

  if (!uploadRes.data.success) {
    throw new AppError(`Flask upload failed: ${uploadRes.data.message}`, 502);
  }

  // step 2 - trigger model run
  const runRes = await axios.post(`${config.FLASK_BASE_URL}/run`, {
    target_chem: targetChem,
    return_format: returnFormat,
  }, {
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    timeout: 120000,
    validateStatus: () => true,
  });

  if (runRes.status !== 200) {
    throw new AppError(`Flask /run failed: ${JSON.stringify(runRes.data)}`, 502);
  }

  return runRes.data;
};


export const sendToPlanner = async (
  kfFilePath: string,  
  heatQuerySchedulePath: string,
  scrapInventoryPath: string,
  gradeFilePath?: string,
  returnFormat: string = "both"
) => {

  if (!fs.existsSync(kfFilePath)) throw new AppError(`KF file not found: ${kfFilePath}`, 404);
  if (!fs.existsSync(heatQuerySchedulePath)) throw new AppError(`Heat Query Schedule file not found: ${heatQuerySchedulePath}`, 404);
  if (!fs.existsSync(scrapInventoryPath)) throw new AppError(`Scrap Inventory file not found: ${scrapInventoryPath}`, 404);
  if (gradeFilePath && !fs.existsSync(gradeFilePath)) throw new AppError(`Grade Specification file not found: ${gradeFilePath}`, 404);
  
  const formData = new FormData();

  formData.append("kf_file", fs.createReadStream(kfFilePath), path.basename(kfFilePath).replace(/^\d+-/, ""));
  formData.append("heat_query", fs.createReadStream(heatQuerySchedulePath), path.basename(heatQuerySchedulePath).replace(/^\d+-/, ""));
  formData.append("scrap_inventory", fs.createReadStream(scrapInventoryPath), path.basename(scrapInventoryPath).replace(/^\d+-/, ""));

  if (gradeFilePath) {
    formData.append("grade_spec", fs.createReadStream(gradeFilePath), path.basename(gradeFilePath).replace(/^\d+-/, ""));
  }

  formData.append("return_format", returnFormat);

  const plannerRes = await axios.post(`${config.FLASK_BASE_URL}/planner`, formData, {
    headers: formData.getHeaders(),
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    timeout: 120000,
    validateStatus: () => true,
  });

  if (plannerRes.status !== 200) {
    throw new AppError(`Flask /planner failed: ${JSON.stringify(plannerRes.data)}`, 502);
  }

  return plannerRes.data;
};