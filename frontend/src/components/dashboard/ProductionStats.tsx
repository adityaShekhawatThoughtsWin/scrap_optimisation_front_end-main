import StatCard from "./StatCard";
function ProductionStats() {
    const statCards = [
        {
            icon: (
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-white" stroke="currentColor" strokeWidth={2.2}>
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                    <polyline points="17 6 23 6 23 12" />
                </svg>
            ),
            iconBg: "bg-emerald-500",
            badge: "+2.3%",
            badgeColor: "text-emerald-500",
            label: "Production Efficiency",
            value: "93.5%",
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-white" stroke="currentColor" strokeWidth={2.2}>
                    <rect x="18" y="3" width="4" height="18" />
                    <rect x="10" y="8" width="4" height="13" />
                    <rect x="2" y="13" width="4" height="8" />
                </svg>
            ),
            iconBg: "bg-sky-400",
            badge: "3 pending",
            badgeColor: "text-orange-400",
            label: "Active Operations",
            value: "12",
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-white" stroke="currentColor" strokeWidth={2.2}>
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <polyline points="3 9 9 9 9 21" />
                    <polyline points="9 9 15 13 21 9" />
                </svg>
            ),
            iconBg: "bg-gradient-to-br from-pink-500 to-orange-400",
            badge: "+52%",
            badgeColor: "text-emerald-500",
            label: "Daily Output",
            value: "8,450",
            unit: "tons",
        },
        {
            icon: (
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-white" stroke="currentColor" strokeWidth={2.2}>
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
            ),
            iconBg: "bg-rose-400",
            badge: "Optimal",
            badgeColor: "text-emerald-500",
            label: "Equipment Health",
            value: "97.2%",
        },
    ];
    return(
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {statCards.map((card, i) => (
                    <StatCard key={i} {...card} />
                ))}
            </div>
    )
}
export default ProductionStats;