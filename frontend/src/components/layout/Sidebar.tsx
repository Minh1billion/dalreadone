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
    <aside className="w-60 min-h-screen bg-[#FAFAFA] border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-200">
        <span className="text-lg font-semibold text-gray-900">DALreaDone</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
              ${isActive
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Sign out */}
      <div className="px-3 py-4 border-t border-gray-200">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}