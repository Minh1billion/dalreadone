import { LayoutGrid, Settings, LogOut } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useLogout } from '../../hooks/useAuth'

const navItems = [
  { to: '/', icon: LayoutGrid, label: 'Projects' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { logout } = useLogout()

  return (
    <aside className="
      flex-none flex flex-col bg-[#FAFAFA] border-r border-gray-200
      w-12 md:w-60
      min-h-screen
      transition-[width] duration-200
    ">
      {/* Logo */}
      <div className="px-3 md:px-5 py-5 border-b border-gray-200 flex items-center gap-3 overflow-hidden">
        {/* Icon — always visible */}
        <div className="flex-none w-6 h-6 bg-gray-900 rounded-md flex items-center justify-center">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
        </div>
        {/* Text — hidden on small screens */}
        <span className="hidden md:block text-lg font-semibold text-gray-900 whitespace-nowrap">DALreaDone</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-1.5 md:px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            title={label}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 px-2.5 py-2 rounded-md text-sm font-medium transition-colors
              ${isActive
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            <>
              <Icon size={16} className="flex-none" />
                <span className="hidden md:block whitespace-nowrap">{label}</span>
                {/* Tooltip for collapsed state */}
                <span className="
                  md:hidden
                  absolute left-full ml-2 px-2 py-1 text-xs rounded-md whitespace-nowrap
                  bg-gray-900 text-white
                  opacity-0 pointer-events-none
                  group-hover:opacity-100
                  transition-opacity z-50
                ">
                  {label}
                </span>
            </>
          </NavLink>
        ))}
      </nav>

      {/* Sign out */}
      <div className="px-1.5 md:px-3 py-4 border-t border-gray-200">
        <button
          onClick={logout}
          title="Sign out"
          className="group relative flex items-center gap-3 px-2.5 py-2 w-full rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
          <LogOut size={16} className="flex-none" />
          <span className="hidden md:block whitespace-nowrap">Sign out</span>
          {/* Tooltip */}
          <span className="
            md:hidden
            absolute left-full ml-2 px-2 py-1 text-xs rounded-md whitespace-nowrap
            bg-gray-900 text-white
            opacity-0 pointer-events-none
            group-hover:opacity-100
            transition-opacity z-50
          ">
            Sign out
          </span>
        </button>
      </div>
    </aside>
  )
}