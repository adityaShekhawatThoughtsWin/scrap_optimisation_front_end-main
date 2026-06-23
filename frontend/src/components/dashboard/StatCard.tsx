import type { ReactNode } from "react";

interface StatCardProps {
    icon: ReactNode;
    iconBg?: string;
    badge?: string;
    badgeColor?: string;
    label: string;
    value: string;
    unit?: string;
  }

function StatCard({ icon, iconBg, badge, badgeColor, label, value, unit }: StatCardProps) {
    return (
      <div className="bg-white rounded-2xl p-5 flex flex-col gap-4 border border-gray-100 shadow-sm hover:-translate-y-0.5 hover:shadow-md transition-all duration-200 cursor-default">
        {/* Top row */}
        <div className="flex items-center justify-between">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconBg}`}>
            {icon}
          </div>
          <span className={`text-sm font-semibold ${badgeColor}`}>{badge}</span>
        </div>
   
        {/* Bottom row */}
        <div>
          <p className="text-gray-400 text-sm font-medium mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900 leading-none flex items-baseline gap-1">
            {value}
            {unit && <span className="text-sm font-medium text-gray-400">{unit}</span>}
          </p>
        </div>
      </div>
    );
  }

export default StatCard;