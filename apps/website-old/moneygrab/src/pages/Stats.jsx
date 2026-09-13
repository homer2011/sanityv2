import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useEvent } from '../context/EventContext.jsx'
import {
  getTeams,
  getTeamMembers,
  getLinked,
  getBosses,
  getBossEhb,
  getRsnKc,
} from '../api.js'
import { Loading, ErrorBox, Empty } from '../components/Status.jsx'
import { computeEhb, normName } from '../lib/moneygrab.js'

export default function Stats() {
  const { selectedEventId } = useEvent()
  const [teams, setTeams] = useState([])
  const [members, setMembers] = useState([])
  const [linked, setLinked] = useState([])
  const [bosses, setBosses] = useState([])
  const [ehb, setEhb] = useState([])
  const [kc, setKc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortKey, setSortKey] = useState('points')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    Promise.all([
      getTeams(selectedEventId),
      getTeamMembers(selectedEventId),
      getLinked(selectedEventId),
      getBosses(selectedEventId),
      getBossEhb(selectedEventId),
      getRsnKc(),
    ])
      .then(([t, m, l, b, e, k]) => {
        if (!active) return
        setTeams(t)
        setMembers(m)
        setLinked(l)
        setBosses(b)
        setEhb(e)
        setKc(k)
      })
      .catch((err) => active && setError(err.message || String(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [selectedEventId])

  const roster = useMemo(() => {
    const teamById = {}
    teams.forEach((t) => (teamById[t.id] = t.name))

    // Key players by their normalized displayName.
    const map = {}
    const add = (key, name, teamId) => {
      if (!map[key]) map[key] = { name, teamId, variants: new Set() }
    }

    members.forEach((m) => {
      const key = normName(m.displayName)
      if (!key) return
      add(key, m.displayName, m.team_id)
      ;[m.displayName, m.rsn, m.mainRSN, m.altRSN].forEach((n) => {
        if (n) map[key].variants.add(normName(n))
      })
    })

    // Include submitters not in the member list.
    linked.forEach((d) => {
      const key = normName(d.submitter)
      if (!key) return
      add(key, d.submitter, d.team_id)
      map[key].variants.add(key)
    })

    // Drops + points per submitter.
    linked.forEach((d) => {
      const key = normName(d.submitter)
      const p = map[key]
      if (!p) return
      p.drops = (p.drops || 0) + 1
      p.points = (p.points || 0) + (Number(d.point_value) || 0)
    })

    // EHB from KC rows, matched to a player via RSN variants.
    kc.forEach((row) => {
      const rsn = normName(row.RSN)
      const val = computeEhb(row, bosses, ehb)
      if (val <= 0) return
      let target = map[rsn]
      if (!target) {
        for (const key of Object.keys(map)) {
          if (map[key].variants.has(rsn)) {
            target = map[key]
            break
          }
        }
      }
      if (target) target.ehb = (target.ehb || 0) + val
    })

    return Object.values(map).map((p) => ({
      name: p.name,
      team_name: teamById[p.teamId] ?? null,
      drops: p.drops || 0,
      points: p.points || 0,
      ehb: p.ehb || 0,
    }))
  }, [teams, members, linked, kc, bosses, ehb])

  const sorted = useMemo(() => {
    const copy = [...roster]
    copy.sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      let cmp = 0
      if (typeof av === 'number' && typeof bv === 'number') cmp = av - bv
      else cmp = String(av ?? '').localeCompare(String(bv ?? ''))
      return sortDir === 'asc' ? cmp : -cmp
    })
    return copy
  }, [roster, sortKey, sortDir])

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  const columns = [
    ['name', 'Player'],
    ['team_name', 'Team'],
    ['drops', 'Drops'],
    ['points', 'Points'],
    ['ehb', 'EHB'],
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-[#00a3d1]">Individual Stats</h1>

      <div className="overflow-x-auto rounded-lg border border-[#224b6d]">
        <table className="min-w-full divide-y divide-[#224b6d] bg-[#122a3d] text-gray-200 text-sm">
          <thead className="bg-[#1a364d]">
            <tr>
              {columns.map(([key, label]) => (
                <th
                  key={key}
                  onClick={() => toggleSort(key)}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white select-none"
                >
                  {label}
                  {sortKey === key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#224b6d]">
            {sorted.map((p) => (
              <tr key={p.name} className="hover:bg-[#1a364d] transition-colors">
                <td className="px-4 py-3">
                  <Link
                    to={`/player/${encodeURIComponent(p.name)}`}
                    className="text-[#00a3d1] hover:underline"
                  >
                    {p.name}
                  </Link>
                </td>
                <td className="px-4 py-3">{p.team_name ?? '—'}</td>
                <td className="px-4 py-3">{p.drops}</td>
                <td className="px-4 py-3 text-yellow-400 font-bold">{p.points}</td>
                <td className="px-4 py-3">{p.ehb.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <Empty message="No players yet." />
          </div>
        )}
      </div>
    </div>
  )
}
