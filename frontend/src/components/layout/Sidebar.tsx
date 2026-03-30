import { useState } from 'react'
import { LayoutGrid, Settings, LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useLogout } from '../../hooks/useAuth'

const navItems = [
  { to: '/', icon: LayoutGrid, label: 'Projects' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { logout } = useLogout()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={`
      relative flex-none flex flex-col bg-[#FAFAFA] border-r border-gray-200
      min-h-screen transition-[width] duration-200
      ${collapsed ? 'w-12' : 'w-12 md:w-60'}
    `}>
      {/* Logo */}
      <div className="px-3 py-5 border-b border-gray-200 flex items-center gap-3 overflow-hidden">
        <div className="flex-none w-6 h-6 bg-gray-900 rounded-md flex items-center justify-center">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
        </div>
        {!collapsed && (
          <span className="hidden md:block text-lg font-semibold text-gray-900 whitespace-nowrap">
            DALreaDone
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-1.5 py-4 space-y-1">
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
            <Icon size={16} className="flex-none" />
            {!collapsed && (
              <span className="hidden md:block whitespace-nowrap">{label}</span>
            )}
            {/* Tooltip when collapsed */}
            {collapsed && (
              <span className="
                absolute left-full ml-2 px-2 py-1 text-xs rounded-md whitespace-nowrap
                bg-gray-900 text-white
                opacity-0 pointer-events-none
                group-hover:opacity-100
                transition-opacity z-50
              ">
                {label}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Sign out */}
      <div className="px-1.5 py-4 border-t border-gray-200">
        <button
          onClick={logout}
          title="Sign out"
          className="group relative flex items-center gap-3 px-2.5 py-2 w-full rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
          <LogOut size={16} className="flex-none" />
          {!collapsed && (
            <span className="hidden md:block whitespace-nowrap">Sign out</span>
          )}
          {collapsed && (
            <span className="
              absolute left-full ml-2 px-2 py-1 text-xs rounded-md whitespace-nowrap
              bg-gray-900 text-white
              opacity-0 pointer-events-none
              group-hover:opacity-100
              transition-opacity z-50
            ">
              Sign out
            </span>
          )}
        </button>
      </div>

      {/* Toggle button */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="
          hidden md:flex
          absolute -right-3 top-18
          w-6 h-6 rounded-full
          bg-white border border-gray-200
          items-center justify-center
          text-gray-400 hover:text-gray-700 hover:border-gray-400
          transition-colors shadow-sm z-10
        "
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  )
}