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
import { Loading, ErrorBox, Empty } from '../components/Status.jsx'
import { computeEhb, dropGp, formatGp, normName } from '../lib/moneygrab.js'

export default function Teams() {
  const { teamId } = useParams()
  const { selectedEventId } = useEvent()

  const [teams, setTeams] = useState([])
  const [members, setMembers] = useState([])
  const [linked, setLinked] = useState([])
  const [bosses, setBosses] = useState([])
  const [ehb, setEhb] = useState([])
  const [kc, setKc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTeamId, setSelectedTeamId] = useState(null)

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
        setSelectedTeamId((prev) => prev ?? (t[0] ? t[0].id : null))
      })
      .catch((err) => active && setError(err.message || String(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [selectedEventId])

  useEffect(() => {
    if (teamId && teams.length) {
      const found = teams.find((t) => String(t.id) === String(teamId))
      if (found) setSelectedTeamId(found.id)
    }
  }, [teamId, teams])

  const team = useMemo(
    () => teams.find((t) => t.id === selectedTeamId),
    [teams, selectedTeamId],
  )

  const roster = useMemo(
    () => members.filter((m) => m.team_id === selectedTeamId),
    [members, selectedTeamId],
  )

  const teamDrops = useMemo(
    () => linked.filter((d) => d.team_id === selectedTeamId),
    [linked, selectedTeamId],
  )

  const memberStats = useMemo(() => {
    return roster.map((m) => {
      const variants = [m.displayName, m.rsn, m.mainRSN, m.altRSN]
        .filter(Boolean)
        .map(normName)
      const drops = teamDrops.filter((d) => variants.includes(normName(d.submitter)))
      const points = drops.reduce((s, d) => s + (Number(d.point_value) || 0), 0)
      let ehbVal = 0
      for (const row of kc) {
        if (variants.includes(normName(row.RSN))) {
          ehbVal += computeEhb(row, bosses, ehb)
        }
      }
      return {
        name: m.displayName,
        drops: drops.length,
        points,
        ehb: ehbVal,
      }
    })
  }, [roster, teamDrops, kc, bosses, ehb])

  const teamMoney = useMemo(
    () => teamDrops.reduce((s, d) => s + dropGp(d), 0),
    [teamDrops],
  )
  const teamPoints = useMemo(
    () => teamDrops.reduce((s, d) => s + (Number(d.point_value) || 0), 0),
    [teamDrops],
  )
  const teamEhb = useMemo(
    () => memberStats.reduce((s, m) => s + m.ehb, 0),
    [memberStats],
  )

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-white">Team:</span>
        <select
          value={selectedTeamId ?? ''}
          onChange={(e) => setSelectedTeamId(Number(e.target.value))}
          className="bg-[#1a364d] border border-[#224b6d] rounded-md p-2 text-white"
        >
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        {team?.image_url && (
          <img
            src={team.image_url}
            alt={team.name}
            className="w-8 h-8 rounded object-cover"
          />
        )}
      </div>

      {!team ? (
        <Empty message="No teams for this event" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-[#1a364d] p-6 rounded-lg shadow-md">
              {team.image_url && (
                <img
                  src={team.image_url}
                  alt={team.name}
                  className="w-24 h-24 rounded-lg object-cover mb-3 mx-auto"
                />
              )}
              <h2 className="text-2xl font-bold text-[#00a3d1] text-center">
                {team.name} Stats
              </h2>
              <div className="space-y-2 text-lg mt-4">
                <div className="flex justify-between">
                  <span>Money (GE)</span>
                  <span className="text-emerald-400 font-bold">
                    {formatGp(teamMoney)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Points</span>
                  <span className="text-yellow-400 font-bold">{teamPoints}</span>
                </div>
                <div className="flex justify-between">
                  <span>Drops</span>
                  <span>{teamDrops.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Team EHB</span>
                  <span>{Math.round(teamEhb)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Captain</span>
                  <span>{team.captain_name ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Co-Captain</span>
                  <span>{team.cocaptain_name ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Members</span>
                  <span>{roster.length}</span>
                </div>
              </div>
            </div>

            <div className="bg-[#1a364d] p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-[#00a3d1] mb-4 text-center">
                Members
              </h2>
              <table className="w-full text-sm bg-[#122a3d]">
                <thead>
                  <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                    <th className="px-2 py-2">Player</th>
                    <th className="px-2 py-2 text-right">Drops</th>
                    <th className="px-2 py-2 text-right">Pts</th>
                    <th className="px-2 py-2 text-right">EHB</th>
                  </tr>
                </thead>
                <tbody>
                  {memberStats.map((m) => (
                    <tr key={m.name} className="border-b border-[#224b6d]/50">
                      <td className="px-2 py-2">
                        <Link
                          to={`/player/${encodeURIComponent(m.name)}`}
                          className="text-[#00a3d1] hover:underline"
                        >
                          {m.name}
                        </Link>
                      </td>
                      <td className="px-2 py-2 text-right">{m.drops}</td>
                      <td className="px-2 py-2 text-right text-yellow-400">
                        {m.points}
                      </td>
                      <td className="px-2 py-2 text-right">{m.ehb.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="lg:col-span-2 bg-[#1a364d] p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-[#00a3d1] mb-4 text-center">
              Drops
            </h2>
            {teamDrops.length === 0 ? (
              <Empty message="No drops linked for this team yet." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm bg-[#122a3d]">
                  <thead>
                    <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                      <th className="px-2 py-2">ID</th>
                      <th className="px-2 py-2">Date</th>
                      <th className="px-2 py-2">Submitter</th>
                      <th className="px-2 py-2">Boss</th>
                      <th className="px-2 py-2">Drop</th>
                      <th className="px-2 py-2 text-right">Points</th>
                      <th className="px-2 py-2 text-right">GE Value</th>
                      <th className="px-2 py-2">Image</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamDrops.map((d) => (
                      <tr key={d.link_id} className="border-b border-[#224b6d]/50">
                        <td className="px-2 py-2">{d.submission_id}</td>
                        <td className="px-2 py-2">
                          {d.reviewedDate
                            ? new Date(d.reviewedDate).toLocaleDateString()
                            : '—'}
                        </td>
                        <td className="px-2 py-2">{d.submitter}</td>
                        <td className="px-2 py-2">{d.boss_name}</td>
                        <td className="px-2 py-2">{d.item_name}</td>
                        <td className="px-2 py-2 text-right text-yellow-400">
                          {d.point_value}
                        </td>
                        <td className="px-2 py-2 text-right text-emerald-400">
                          {d.ge_value != null
                            ? formatGp(d.ge_value)
                            : d.value != null
                              ? formatGp(d.value)
                              : '—'}
                        </td>
                        <td className="px-2 py-2">
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
      )}
    </div>
  )
}
