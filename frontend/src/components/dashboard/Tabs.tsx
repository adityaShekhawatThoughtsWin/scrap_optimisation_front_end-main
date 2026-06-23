import { NavLink } from 'react-router-dom'
import { images } from '../../utils/images'

const dashboardTabs = [
  { label: 'Home', path: '/dashboard', icon: images.homeIcon },
  { label: 'Input', path: '/dashboard/input', icon: images.calculatorIcon },
] as const

function Tabs({ rightComponent }: { rightComponent: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-6 py-4">
      <nav className="flex items-center gap-4" aria-label="Dashboard sections">
        {dashboardTabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end
            className={({ isActive }) =>
              [
                'inline-flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold transition-colors duration-200',
                isActive
                  ? 'bg-[#17479E0F] text-[#0F3173] font-bold'
                  : 'text-text-secondary hover:text-text-primary',
              ].join(' ')
            }
          >
            <img src={tab.icon} alt={tab.label} className="w-4 h-4" />
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <div className="">
        {rightComponent}
      </div>
    </div>
  )
}

// function TabsWithButton({buttonText,onButtonClick}: {buttonText: string,onButtonClick: () => void}) {
//   return (
//     <div className="flex justify-between py-4 items-center px-6">
//       <Tabs />
//       <Button className="rounded-lg px-2 py-3.5 text-sm" variant="secondary" onClick={onButtonClick}>
//         + {buttonText}
//       </Button>
//     </div>
//   );
// }
export default Tabs;