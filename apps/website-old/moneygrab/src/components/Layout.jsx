import { NavLink, Outlet } from 'react-router-dom'
import { useEvent } from '../context/EventContext.jsx'

const NAV_LINKS = [
  ['/', 'Overview'],
  ['/drops', 'Drops'],
  ['/bosses', 'Bosses'],
  ['/stats', 'Stats'],
  ['/teams', 'Teams'],
  ['/builder', 'Builder'],
]

export default function Layout() {
  const { events, selectedEventId, setSelectedEventId } = useEvent()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#1a364d] text-white shadow-lg">
        <nav className="container mx-auto px-4 py-4 flex justify-between items-center flex-wrap gap-3">
          <NavLink
            to="/"
            className="text-2xl font-bold hover:text-[#00a3d1] transition-colors"
          >
            Money Grab
          </NavLink>

          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedEventId || ''}
              onChange={(e) => setSelectedEventId(parseInt(e.target.value, 10) || null)}
              className="bg-[#122a3d] border border-[#224b6d] rounded-md p-2 text-white text-sm"
            >
              {events.map((event) => (
                <option key={event.id} value={event.id}>
                  {event.name}
                </option>
              ))}
            </select>

            {NAV_LINKS.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md transition-colors text-sm ${
                    isActive
                      ? 'bg-[#00a3d1] text-white'
                      : 'hover:bg-[#224b6d]'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>

      <main className="flex-grow container mx-auto px-4 py-8">
        <Outlet />
      </main>

      <footer className="bg-[#1a364d] text-white text-center p-4 shadow-inner mt-8">
        <p>© {new Date().getFullYear()} Sanity OSRS clan</p>
      </footer>
    </div>
  )
}
