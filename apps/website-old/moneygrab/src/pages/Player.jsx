import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useEvent } from '../context/EventContext.jsx'
import {
  getTeams,
  getTeamMembers,
  getLinked,
  getBosses,
  getBossEhb,
  getRsnKc,
} from '../api.js'
import { Loading, ErrorBox } from '../components/Status.jsx'
import { computeEhb, dropGp, formatGp, normName } from '../lib/moneygrab.js'

export default function Player() {
  const { playerName } = useParams()
  const { selectedEventId } = useEvent()
  const decoded = decodeURIComponent(playerName || '')

  const [teams, setTeams] = useState([])
  const [members, setMembers] = useState([])
  const [linked, setLinked] = useState([])
  const [bosses, setBosses] = useState([])
  const [ehb, setEhb] = useState([])
  const [kc, setKc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  const member = useMemo(() => {
    const key = normName(decoded)
    return members.find((m) => normName(m.displayName) === key)
  }, [members, decoded])

  const variants = useMemo(() => {
    const set = new Set([normName(decoded)])
    if (member) {
      ;[member.displayName, member.rsn, member.mainRSN, member.altRSN].forEach(
        (n) => n && set.add(normName(n)),
      )
    }
    return set
  }, [member, decoded])

  const playerDrops = useMemo(
    () => linked.filter((d) => variants.has(normName(d.submitter))),
    [linked, variants],
  )

  const teamId = member?.team_id ?? playerDrops[0]?.team_id ?? null
  const teamName = useMemo(() => {
    const t = teams.find((x) => x.id === teamId)
    return t?.name ?? null
  }, [teams, teamId])

  const points = useMemo(
    () => playerDrops.reduce((s, d) => s + (Number(d.point_value) || 0), 0),
    [playerDrops],
  )
  const money = useMemo(
    () => playerDrops.reduce((s, d) => s + dropGp(d), 0),
    [playerDrops],
  )
  const ehbVal = useMemo(() => {
    let total = 0
    for (const row of kc) {
      if (variants.has(normName(row.RSN))) {
        total += computeEhb(row, bosses, ehb)
      }
    }
    return total
  }, [kc, variants, bosses, ehb])

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-bold text-[#00a3d1]">{decoded}</h1>
        {teamId && (
          <Link
            to={`/teams/${teamId}`}
            className="text-sm text-gray-400 hover:text-white underline"
          >
            {teamName ?? 'Team'}
          </Link>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          ['Drops', playerDrops.length],
          ['Points', points],
          ['Money (GE)', formatGp(money)],
          ['EHB', ehbVal.toFixed(2)],
        ].map(([label, value]) => (
          <div key={label} className="bg-[#1a364d] p-4 rounded-lg shadow-md text-center">
            <div className="text-gray-400 text-xs uppercase">{label}</div>
            <div className="text-2xl font-bold text-[#00a3d1] mt-1">{value}</div>
          </div>
        ))}
      </div>

      <div className="bg-[#1a364d] p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-bold text-[#00a3d1] mb-4">Drops</h2>
        {playerDrops.length === 0 ? (
          <p className="text-gray-400 text-sm">No drops for this player.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm bg-[#122a3d]">
              <thead>
                <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Boss</th>
                  <th className="px-3 py-2">Drop</th>
                  <th className="px-3 py-2 text-right">Points</th>
                  <th className="px-3 py-2 text-right">GE Value</th>
                  <th className="px-3 py-2">Image</th>
                </tr>
              </thead>
              <tbody>
                {playerDrops.map((d) => (
                  <tr key={d.link_id} className="border-b border-[#224b6d]/50">
                    <td className="px-3 py-2">{d.submission_id}</td>
                    <td className="px-3 py-2">
                      {d.reviewedDate
                        ? new Date(d.reviewedDate).toLocaleDateString()
                        : '—'}
                    </td>
                    <td className="px-3 py-2">{d.boss_name}</td>
                    <td className="px-3 py-2">{d.item_name}</td>
                    <td className="px-3 py-2 text-right text-yellow-400">
                      {d.point_value}
                    </td>
                    <td className="px-3 py-2 text-right text-emerald-400">
                      {d.ge_value != null
                        ? formatGp(d.ge_value)
                        : d.value != null
                          ? formatGp(d.value)
                          : '—'}
                    </td>
                    <td className="px-3 py-2">
                      {d.imageUrl ? (
                        <a
                          href={d.imageUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#00a3d1] hover:underline"
                        >
                          View
                        </a>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
