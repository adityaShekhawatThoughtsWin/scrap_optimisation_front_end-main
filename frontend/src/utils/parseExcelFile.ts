import * as XLSX from "xlsx/xlsx.mjs";

export async function parseExcelFile(file: File): Promise<Record<string, unknown>[]> {
    const buffer = await file.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: "array" });
    const firstSheetName = workbook.SheetNames[0];

    if (!firstSheetName) {
        return [];
    }

    const worksheet = workbook.Sheets[firstSheetName];
    const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(worksheet, { defval: "" });

    return rows;
}
