import { useState } from "react";
import CustomCalendar from "./CustomCalendar";

function formatDate(date: Date): string {
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const months = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

  const dayName = days[date.getDay()];
  const day = date.getDate();
  const month = months[date.getMonth()];

  const suffix =
    day % 10 === 1 && day !== 11 ? "st" :
    day % 10 === 2 && day !== 12 ? "nd" :
    day % 10 === 3 && day !== 13 ? "rd" : "th";

  return `${dayName}, ${day}${suffix} ${month}`;
}

function DatePicker() {
  const [date, setDate] = useState<Date>(new Date());
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const handleChoose = (date: Date) => {
    setDate(date);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setIsOpen(false);
  };

  return (
    <div className="relative w-full">
      {/* Styled date trigger */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-1.5 text-brand-primary font-medium text-[15px] hover:opacity-80 transition-opacity"
      >
        <span>{formatDate(date)}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`transition-transform duration-200 ${isOpen ? "rotate-180" : "rotate-0"}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Calendar */}
      {isOpen && (
        <div className=" absolute top-5 right-5 z-50 ">
          <CustomCalendar
            onCancel={handleCancel}
            onChoose={handleChoose}
            date={date}
          />
        </div>
      )}
    </div>
  );
}

export default DatePicker;