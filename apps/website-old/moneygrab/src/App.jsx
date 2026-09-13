import { Routes, Route } from 'react-router-dom'
import { EventProvider } from './context/EventContext.jsx'
import Layout from './components/Layout.jsx'
import Overview from './pages/Overview.jsx'
import Drops from './pages/Drops.jsx'
import Bosses from './pages/Bosses.jsx'
import Stats from './pages/Stats.jsx'
import Teams from './pages/Teams.jsx'
import Player from './pages/Player.jsx'
import Builder from './pages/Builder.jsx'

export default function App() {
  return (
    <EventProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/drops" element={<Drops />} />
          <Route path="/bosses" element={<Bosses />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/teams/:teamId" element={<Teams />} />
          <Route path="/player/:playerName" element={<Player />} />
          <Route path="/builder" element={<Builder />} />
        </Route>
      </Routes>
    </EventProvider>
  )
}
