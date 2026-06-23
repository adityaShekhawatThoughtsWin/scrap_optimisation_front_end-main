import { useMemo, useState } from "react";

interface CustomTableProps {
    title: string;
    data: Record<string, unknown>[];
}

const formatHeader = (key: string) =>
    key
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/[_-]/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

function CustomTableWithData({ title, data }: CustomTableProps) {
    const [searchTerm, setSearchTerm] = useState("");

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

    return (
        <div className="w-full rounded-md p-3 text-zinc-900">
            <h1 className="mb-3 text-lg font-bold uppercase tracking-wide text-[#303030]">{title}</h1>

            <div className="mb-4 max-w-lg rounded-lg border border-zinc-300 px-3 py-2 text-zinc-700">
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search in table"
                    className="w-full bg-transparent text-sm text-zinc-700 outline-none placeholder:text-zinc-400"
                />
            </div>

            <div className="overflow-x-auto rounded-lg border border-zinc-300">
                <table className="min-w-full border-collapse text-sm text-zinc-800">
                    <thead>
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
                                    No data found
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default CustomTableWithData;