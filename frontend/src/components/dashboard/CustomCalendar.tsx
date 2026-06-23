import { useState } from "react";

const DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];


function isSameDay(a, b) {
  return (
    a && b &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}



export default function CustomCalendar({ onCancel, onChoose, date }: { onCancel: () => void, onChoose: (date: Date) => void, date: Date }) {
  const today = new Date(); // shown with blue outline
  const [current, setCurrent] = useState(date);
  const [selected, setSelected] = useState(date);

  const year = current.getFullYear();
  const month = current.getMonth();

  const firstDay = new Date(year, month, 1).getDay();
  const startOffset = firstDay === 0 ? 6 : firstDay - 1; // Mon-first
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevMonthDays = new Date(year, month, 0).getDate();

  const cells = [];

  for (let i = startOffset - 1; i >= 0; i--)
    cells.push({ day: prevMonthDays - i, currentMonth: false });

  for (let d = 1; d <= daysInMonth; d++)
    cells.push({ day: d, currentMonth: true });

  const remaining = 7 - (cells.length % 7);
  if (remaining < 7)
    for (let d = 1; d <= remaining; d++)
      cells.push({ day: d, currentMonth: false });

  const handleChoose = () => onChoose?.(selected);

  return (
    <div className="bg-white rounded-[20px] p-6 w-[340px] shadow-lg font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <button
          onClick={() => setCurrent(new Date(year, month - 1, 1))}
          className="text-2xl text-gray-800 px-3 py-1 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Previous month"
        >
          ‹
        </button>
        <span className="text-[17px] font-semibold text-gray-900">
          {MONTHS[month]} {year}
        </span>
        <button
          onClick={() => setCurrent(new Date(year, month + 1, 1))}
          className="text-2xl text-gray-800 px-3 py-1 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      {/* Day labels */}
      <div className="grid grid-cols-7 mb-1">
        {DAYS.map((d) => (
          <div key={d} className="text-center text-[13px] text-gray-400 pb-2">
            {d}
          </div>
        ))}

        {/* Day cells */}
        {cells.map((cell, i) => {
          const date = cell.currentMonth ? new Date(year, month, cell.day) : null;
          const isSelected = isSameDay(date, selected);
          const isToday = isSameDay(date, today) && !isSelected;

          return (
            <div
              key={i}
              onClick={() =>
                cell.currentMonth && setSelected(new Date(year, month, cell.day))
              }
              className={[
                "relative flex flex-col items-center justify-center aspect-square rounded-[10px] m-[2px] transition-colors",
                cell.currentMonth ? "cursor-pointer" : "cursor-default",
                isSelected
                  ? "bg-brand-primary"
                  : isToday
                  ? "bg-blue-50 border-2 border-blue-300"
                  : cell.currentMonth
                  ? "bg-gray-100 hover:bg-gray-200"
                  : "bg-transparent",
              ].join(" ")}
            >
              <span
                className={[
                  "text-[15px] font-medium leading-none",
                  isSelected
                    ? "text-white"
                    : isToday
                    ? "text-blue-500"
                    : cell.currentMonth
                    ? "text-gray-900"
                    : "text-gray-300",
                ].join(" ")}
              >
                {cell.day}
              </span>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex gap-2.5 mt-5">
        <button
          onClick={onCancel}
          className="flex-1 py-[14px] bg-gray-200 text-gray-500 rounded-[14px] text-base font-normal hover:bg-gray-300 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleChoose}
          className="flex-2 py-[14px] bg-brand-primary text-white rounded-[14px] text-base font-semibold hover:bg-brand-primary-dark transition-colors"
        >
          Choose Date
        </button>
      </div>
    </div>
  );
}