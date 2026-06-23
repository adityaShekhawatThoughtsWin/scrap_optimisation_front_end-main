import NotificationsOutlinedIcon from '@mui/icons-material/NotificationsOutlined'
import { useState } from 'react'
import { images } from '../../utils/images'

type ControlMode = 'manual' | 'auto'

export function Navbar() {
  const [notifications, setNotifications] = useState(2)
  const [username, setUsername] = useState('Garvit Singhal ')
  const [mode, setMode] = useState<'manual' | 'auto'>('manual')

  return (
    <header className="flex h-14 items-center justify-between bg-brand-primary px-4 py-4">
      <img src={images.jswSteelWhiteLogo} alt="JSW Steel Logo" className="w-30 h-10 object-contain rounded-lg" />
   
      <div className="flex items-center gap-5">
      <span className="text-text-inverse h-10 flex items-center text-2xl font-medium leading-none">Scrap Mix Planner</span>

         {/* <div
          role="group"
          aria-label="Control mode"
          className="relative flex rounded-full bg-text-inverse p-1 "
        >
          <span
            aria-hidden
            className={[
              'pointer-events-none absolute inset-y-1 left-1 w-[calc(50%-0.25rem)] rounded-full bg-brand-danger',
              'transition-transform duration-200 ease-in-out motion-reduce:transition-none',
              mode === 'auto' ? 'translate-x-full' : 'translate-x-0',
            ].join(' ')}
          />
          <button
            type="button"
            onClick={() => setMode('manual')}
            className={[
              'relative z-10 rounded-full px-4 py-1.5 text-sm font-medium transition-colors duration-200 w-1/2 flex items-center justify-center text-center',
              mode === 'manual'
                ? 'text-text-inverse'
                : 'text-brand-primary-dark',
            ].join(' ')}
          >
            Manual
          </button>
          <button
            type="button"
            onClick={() => setMode('auto')}
            className={[
              'relative z-10 rounded-full px-4 py-1.5 text-sm font-medium transition-colors duration-200 w-1/2 flex items-center justify-center text-center',
              mode === 'auto'
                ? 'text-text-inverse'
                : 'text-brand-primary-dark',
            ].join(' ')}
          >
            Auto
          </button>
        </div>  */}

        {/* <button
          type="button"
          aria-label="Notifications"
          className="relative flex items-center justify-center text-text-inverse"
        >
          <NotificationsOutlinedIcon sx={{ fontSize: 24 }} />
          {notifications > 0 && (
            <span
              className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-brand-danger"
              aria-hidden
            />
          )}
        </button> */}

        {/* <div
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-text-inverse text-sm font-semibold text-brand-primary"
          aria-label="User profile"
        >
            {username.split(' ').map((name) => name.charAt(0).toUpperCase()).join('').slice(0, 2)}
        </div> */}
      </div>
      <div className="flex items-center ">
        <img src={images.tejasLogo} alt="Tejas Logo" className="w-15 h-10 object-contain" />
        <img src={images.tejasNameLogo} alt="Tejas Name Logo" className="w-30 h-10 object-contain" />
      </div>
    </header>
  )
}
