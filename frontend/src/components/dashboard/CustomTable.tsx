import { useMemo, useRef, useState } from "react";
import { parseExcelFile } from "../../utils/parseExcelFile";

interface CustomTableProps {
    title: string;
}

const formatHeader = (key: string) =>
    key
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/[_-]/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

function CustomTable({ title }: CustomTableProps) {
    const [data, setData] = useState<Record<string, unknown>[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [isParsing, setIsParsing] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const columns = useMemo(() => {
        const keySet = new Set<string>();
        data.forEach((item) => Object.keys(item).forEach((key) => keySet.add(key)));
        return Array.from(keySet);
    }, [data]);

    const filteredData = useMemo(() => {
        const normalizedSearch = searchTerm.trim().toLowerCase();
        if (!normalizedSearch) return data;

        return data.filter((row) =>
            columns.some((column) => {
                const value = row[column];
                return String(value ?? "")
                    .toLowerCase()
                    .includes(normalizedSearch);
            }),
        );
    }, [columns, data, searchTerm]);

    const hasUploadedData = data.length > 0;

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleRemoveFile = () => {
        setData([]);
        setSearchTerm("");
        setUploadError(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        event.target.value = "";

        if (!file) return;

        setUploadError(null);
        setIsParsing(true);

        try {
            const parsedRows = await parseExcelFile(file);

            if (parsedRows.length === 0) {
                setUploadError("The selected file has no data.");
                return;
            }

            setData(parsedRows);
            setSearchTerm("");
        } catch {
            setUploadError("Could not read the Excel file. Please try a valid .xlsx or .xls file.");
        } finally {
            setIsParsing(false);
        }
    };

    const emptyMessage =
        data.length === 0 ? "Upload an Excel file to populate this table." : "No data found";

    return (
        <div className="w-full rounded-md p-3 text-zinc-900">
            <h1 className="mb-3 text-lg font-bold uppercase tracking-wide text-[#303030]">{title}</h1>

            <div className="mb-4 flex items-center gap-3 justify-between">
                <div className="min-w-0 flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-zinc-700 max-w-1/3">
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(event) => setSearchTerm(event.target.value)}
                        placeholder="Search in table"
                        className="w-full bg-transparent text-sm text-zinc-700 outline-none placeholder:text-zinc-400"
                    />
                </div>
                <div className="flex shrink-0 items-center gap-2">
                    <button
                        type="button"
                        onClick={handleUploadClick}
                        disabled={isParsing}
                        className="rounded-lg border border-brand-primary bg-brand-primary px-4 py-2 text-sm font-medium text-zinc-100 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {isParsing ? "Uploading..." : "Upload Excel"}
                    </button>
                    {hasUploadedData && (
                        <button
                            type="button"
                            onClick={handleRemoveFile}
                            disabled={isParsing}
                            className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            Remove Excel
                        </button>
                    )}
                </div>

                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                    onChange={handleFileChange}
                    className="hidden"
                />
            </div>

            {uploadError && <p className="mb-3 text-sm text-red-600">{uploadError}</p>}

            <div className="overflow-x-auto rounded-lg border border-zinc-300">
                <table className="min-w-full border-collapse text-sm text-zinc-800">
                    <thead>
                        {columns.length > 0 && (
                            <tr className="bg-linear-to-b from-brand-primary to-brand-primary-dark text-zinc-100">
                                {columns.map((column) => (
                                    <th
                                        key={column}
                                        className="border border-brand-primary px-4 py-3 text-left font-medium"
                                    >
                                        <span className="flex items-center justify-between gap-3">
                                            {formatHeader(column)}
                                            <svg
                                                viewBox="0 0 24 24"
                                                className="h-3.5 w-3.5 text-brand-primary"
                                                fill="none"
                                                stroke="white"
                                                strokeWidth="2"
                                            >
                                                <path d="M4 5h16l-6 7v6l-4 2v-8L4 5z" />
                                            </svg>
                                        </span>
                                    </th>
                                ))}
                            </tr>
                        )}
                    </thead>
                    <tbody>
                        {filteredData.length > 0 ? (
                            filteredData.map((row, rowIndex) => (
                                <tr key={`${rowIndex}-${Object.values(row).join("-")}`} className="">
                                    {columns.map((column) => (
                                        <td
                                            key={`${column}-${rowIndex}`}
                                            className="border border-zinc-300 px-4 py-3 text-zinc-800"
                                        >
                                            {String(row[column] ?? "")}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td
                                    colSpan={Math.max(columns.length, 1)}
                                    className="border border-zinc-300 bg-zinc-100 px-4 py-6 text-center text-zinc-500"
                                >
                                    {emptyMessage}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default CustomTable;
