import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useEvent } from '../context/EventContext.jsx'
import {
  getTeams,
  getTeamMembers,
  getLinked,
  getDrops,
  getBosses,
  getBossEhb,
  getRsnKc,
  getBossImages,
  getDiscordProfiles,
} from '../api.js'
import { Loading, ErrorBox } from '../components/Status.jsx'
import { computeEhb, dropGp, formatGp, normName } from '../lib/moneygrab.js'

const CHART_COLORS = [
  '#00a3d1',
  '#e74c3c',
  '#2ecc71',
  '#f39c12',
  '#9b59b6',
  '#1abc9c',
  '#e67e22',
  '#3498db',
  '#e84393',
  '#a29bfe',
]

export default function Overview() {
  const { selectedEventId, selectedEvent } = useEvent()
  const [teams, setTeams] = useState([])
  const [members, setMembers] = useState([])
  const [linked, setLinked] = useState([])
  const [bosses, setBosses] = useState([])
  const [ehb, setEhb] = useState([])
  const [kc, setKc] = useState([])
  const [bossImages, setBossImages] = useState([])
  const [profiles, setProfiles] = useState([])
  const [drops, setDrops] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [chartMode, setChartMode] = useState('money')

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
      getBossImages(),
      getDiscordProfiles(),
      getDrops(selectedEventId),
    ])
      .then(([t, m, l, b, e, k, bi, p, dr]) => {
        if (!active) return
        setTeams(t)
        setMembers(m)
        setLinked(l)
        setBosses(b)
        setEhb(e)
        setKc(k)
        setBossImages(bi)
        setProfiles(p)
        setDrops(dr)
      })
      .catch((err) => active && setError(err.message || String(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [selectedEventId])

  const start = useMemo(
    () => (selectedEvent ? new Date(selectedEvent.start_date) : null),
    [selectedEvent],
  )
  const end = useMemo(
    () => (selectedEvent ? new Date(selectedEvent.end_date) : null),
    [selectedEvent],
  )

  const bossImagesByName = useMemo(() => {
    const m = {}
    bossImages.forEach((b) => {
      if (b.boss_name) m[normName(b.boss_name)] = b.image_url
    })
    return m
  }, [bossImages])

  const profileByName = useMemo(() => {
    const m = {}
    profiles.forEach((p) => {
      if (p.displayName) m[normName(p.displayName)] = p.discordProfileImageUrl
    })
    return m
  }, [profiles])

  const nameToTeam = useMemo(() => {
    const map = {}
    members.forEach((m) => {
      ;[m.displayName, m.rsn, m.mainRSN, m.altRSN].forEach((n) => {
        if (n) map[normName(n)] = m.team_id
      })
    })
    return map
  }, [members])

  const teamStats = useMemo(() => {
    return teams.map((t) => {
      const ds = linked.filter((d) => d.team_id === t.id)
      const drops = ds.length
      const points = ds.reduce((s, d) => s + (Number(d.point_value) || 0), 0)
      const money = ds.reduce((s, d) => s + dropGp(d), 0)
      return {
        team_id: t.id,
        team_name: t.name,
        image_url: t.image_url,
        captain: t.captain_name,
        co_captain: t.cocaptain_name,
        drops,
        points,
        money,
      }
    })
  }, [teams, linked])

  const playerPoints = useMemo(() => {
    const map = {}
    linked.forEach((d) => {
      const name = normName(d.submitter)
      if (!name) return
      if (!map[name]) map[name] = { name: d.submitter, drops: 0, points: 0 }
      map[name].drops += 1
      map[name].points += Number(d.point_value) || 0
    })
    return Object.values(map)
  }, [linked])

  const playerEhb = useMemo(() => {
    const rows = kc.map((row) => ({
      name: row.RSN,
      val: computeEhb(row, bosses, ehb),
    }))
    return rows.filter((r) => r.val > 0)
  }, [kc, bosses, ehb])

  const leaderboard = useMemo(
    () =>
      [...teamStats].sort(
        (a, b) => b.money - a.money || b.points - a.points || b.drops - a.drops,
      ),
    [teamStats],
  )

  const topPoints = useMemo(
    () => [...playerPoints].sort((a, b) => b.points - a.points).slice(0, 5),
    [playerPoints],
  )
  const topEhb = useMemo(
    () => [...playerEhb].sort((a, b) => b.val - a.val).slice(0, 5),
    [playerEhb],
  )

  const chartSeries = useMemo(() => {
    return teams
      .map((t, i) => {
        const ds = (linked.filter((d) => d.team_id === t.id))
          .slice()
          .sort((a, b) => new Date(a.reviewedDate) - new Date(b.reviewedDate))
        const pts = []
        if (start) pts.push({ t: start.getTime(), v: 0 })
        let cum = 0
        for (const d of ds) {
          const ts = new Date(d.reviewedDate).getTime()
          if (Number.isNaN(ts)) continue
          cum += chartMode === 'money' ? dropGp(d) : Number(d.point_value) || 0
          pts.push({ t: ts, v: cum })
        }
        return { name: t.name, color: CHART_COLORS[i % CHART_COLORS.length], pts }
      })
      .filter((s) => s.pts.length > 1)
  }, [teams, linked, chartMode, start])

  const dropSummary = useMemo(() => {
    const countMap = {}
    linked.forEach((l) => {
      if (!countMap[l.drop_id]) countMap[l.drop_id] = {}
      countMap[l.drop_id][l.team_id] = (countMap[l.drop_id][l.team_id] || 0) + 1
    })
    return drops.map((d) => ({
      ...d,
      counts: teams.map((t) => countMap[d.id]?.[t.id] || 0),
    }))
  }, [drops, linked, teams])

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  const now = new Date()
  const remainingMs = end && end > now ? end - now : null
  const hoursRemaining = remainingMs != null ? remainingMs / 36e5 : null
  const remainingText =
    remainingMs != null
      ? `${Math.floor(remainingMs / 36e5)}h ${Math.floor(
          (remainingMs % 36e5) / 6e4,
        )}m remaining`
      : null

  const fmtDateTime = (d) => {
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  const totalMoney = teamStats.reduce((s, t) => s + t.money, 0)

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-[#00a3d1]">Money Grab</h1>
        {selectedEvent && (
          <div className="mt-1 text-gray-300 text-lg">{selectedEvent.name}</div>
        )}
        {start && end && (
          <div className="mt-2 text-gray-400 text-sm space-x-4">
            <span>
              {fmtDateTime(start)} → {fmtDateTime(end)}
            </span>
            {hoursRemaining != null && (
              <span
                className={
                  hoursRemaining < 24 ? 'text-red-400 font-bold' : 'text-[#00a3d1]'
                }
              >
                {remainingText}
              </span>
            )}
          </div>
        )}

        {bosses.length > 0 && (
          <div className="flex justify-center gap-4 mt-4 flex-wrap">
            {bosses.map((b) => {
              const url = bossImagesByName[normName(b.boss_name)]
              return url ? (
                <img
                  key={b.id}
                  src={url}
                  alt={b.boss_name}
                  title={b.boss_name}
                  className="w-16 h-16 rounded-lg object-cover ring-2 ring-[#00a3d1] bg-[#122a3d]"
                />
              ) : null
            })}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start">
        <div className="xl:col-span-2 bg-[#1a364d] p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold text-[#00a3d1] text-center">
              Leaderboard
            </h2>
            <span className="text-sm text-gray-400">
              Total made: <span className="text-yellow-400">{formatGp(totalMoney)}</span>
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm bg-[#122a3d]">
              <thead>
                <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                  <th className="px-4 py-3 w-10">#</th>
                  <th className="px-4 py-3">Team</th>
                  <th className="px-4 py-3">Captain</th>
                  <th className="px-4 py-3 text-right">Drops</th>
                  <th className="px-4 py-3 text-right">Points</th>
                  <th className="px-4 py-3 text-right">Money (GE)</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((t, i) => (
                  <tr
                    key={t.team_id}
                    className="border-b border-[#224b6d] hover:bg-[#224b6d]/40"
                  >
                    <td className="px-4 py-3 font-bold text-gray-400">{i + 1}</td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/teams/${t.team_id}`}
                        className="flex items-center gap-2 hover:underline"
                      >
                        {t.image_url ? (
                          <img
                            src={t.image_url}
                            alt={t.team_name}
                            className="w-6 h-6 rounded object-cover"
                          />
                        ) : null}
                        <span className="text-[#00a3d1]">{t.team_name}</span>
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      {t.captain ? (
                        <span className="flex items-center gap-2">
                          {profileByName[normName(t.captain)] ? (
                            <img
                              src={profileByName[normName(t.captain)]}
                              alt={t.captain}
                              className="w-5 h-5 rounded-full object-cover"
                            />
                          ) : null}
                          {t.captain}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">{t.drops}</td>
                    <td className="px-4 py-3 text-right text-yellow-400">
                      {t.points}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">
                      {formatGp(t.money)}
                    </td>
                  </tr>
                ))}
                {leaderboard.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      No teams yet for this event.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <div className="bg-[#1a364d] p-4 rounded-lg shadow-md">
            <h3 className="text-sm font-bold text-[#00a3d1] mb-2 text-center">
              Top 5 Points (Players)
            </h3>
            <table className="w-full text-sm bg-[#122a3d]">
              <thead>
                <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                  <th className="px-2 py-1">Player</th>
                  <th className="px-2 py-1 text-right">Drops</th>
                  <th className="px-2 py-1 text-right">Pts</th>
                </tr>
              </thead>
              <tbody>
                {topPoints.map((p) => (
                  <tr key={p.name} className="border-b border-[#224b6d]/50">
                    <td className="px-2 py-1">
                      <Link
                        to={`/player/${encodeURIComponent(p.name)}`}
                        className="flex items-center gap-2 text-[#00a3d1] hover:underline"
                      >
                        {profileByName[normName(p.name)] ? (
                          <img
                            src={profileByName[normName(p.name)]}
                            alt={p.name}
                            className="w-5 h-5 rounded-full object-cover"
                          />
                        ) : null}
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-2 py-1 text-right">{p.drops}</td>
                    <td className="px-2 py-1 text-right text-yellow-400">
                      {p.points}
                    </td>
                  </tr>
                ))}
                {topPoints.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-2 py-4 text-center text-gray-500">
                      No drops linked yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="bg-[#1a364d] p-4 rounded-lg shadow-md">
            <h3 className="text-sm font-bold text-[#00a3d1] mb-2 text-center">
              Top 5 EHB
            </h3>
            <table className="w-full text-sm bg-[#122a3d]">
              <thead>
                <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                  <th className="px-2 py-1">Player</th>
                  <th className="px-2 py-1 text-right">EHB</th>
                </tr>
              </thead>
              <tbody>
                {topEhb.map((p) => (
                  <tr key={p.name} className="border-b border-[#224b6d]/50">
                    <td className="px-2 py-1">
                      <Link
                        to={`/player/${encodeURIComponent(p.name)}`}
                        className="flex items-center gap-2 text-[#00a3d1] hover:underline"
                      >
                        {profileByName[normName(p.name)] ? (
                          <img
                            src={profileByName[normName(p.name)]}
                            alt={p.name}
                            className="w-5 h-5 rounded-full object-cover"
                          />
                        ) : null}
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-2 py-1 text-right">{p.val.toFixed(2)}</td>
                  </tr>
                ))}
                {topEhb.length === 0 && (
                  <tr>
                    <td colSpan={2} className="px-2 py-4 text-center text-gray-500">
                      No EHB data.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="bg-[#1a364d] p-6 rounded-lg shadow-md">
        <h3 className="text-2xl font-bold text-[#00a3d1] mb-4 text-center">
          Drops Collected
        </h3>
        {drops.length === 0 ? (
          <p className="text-gray-500 text-center">No drops configured for this event.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm bg-[#122a3d]">
              <thead>
                <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                  <th className="px-3 py-2">Item</th>
                  <th className="px-3 py-2">Boss</th>
                  {teams.map((t) => (
                    <th key={t.id} className="px-3 py-2 text-right">
                      {t.name}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {dropSummary.map((d) => (
                  <tr
                    key={d.id}
                    className="border-b border-[#224b6d] hover:bg-[#224b6d]/40"
                  >
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        {d.image_url ? (
                          <img
                            src={d.image_url}
                            alt={d.item_name}
                            className="w-6 h-6 object-contain shrink-0"
                            loading="lazy"
                          />
                        ) : null}
                        <span>{d.item_name}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2">{d.boss_name}</td>
                    {d.counts.map((c, i) => (
                      <td
                        key={i}
                        className={`px-3 py-2 text-right ${
                          c > 0 ? 'font-bold text-[#00a3d1]' : 'text-gray-500'
                        }`}
                      >
                        {c}
                      </td>
                    ))}
                    <td className="px-3 py-2 text-right font-bold">
                      {d.counts.reduce((s, c) => s + c, 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-[#1a364d] p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h3 className="text-2xl font-bold text-[#00a3d1]">Over Time</h3>
          <div className="flex gap-2">
            {[
              ['money', 'Money'],
              ['points', 'Points'],
            ].map(([key, label]) => (
              <button
                key={key}
                onClick={() => setChartMode(key)}
                className={`px-4 py-2 rounded-md text-sm font-bold transition-colors ${
                  chartMode === key
                    ? 'bg-[#00a3d1] text-white'
                    : 'bg-[#122a3d] text-gray-300 hover:bg-[#224b6d]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <OverTimeChart series={chartSeries} start={start} end={end} mode={chartMode} />
      </div>
    </div>
  )
}

function OverTimeChart({ series, start, end, mode }) {
  if (!series.length) {
    return <p className="text-gray-500 text-center py-4">No data to chart yet.</p>
  }

  const nowMs = Date.now()
  const x0 = start
    ? start.getTime()
    : Math.min(...series.flatMap((s) => s.pts.map((p) => p.t)))
  const x1 = Math.min(nowMs, end ? end.getTime() : nowMs)
  if (x1 <= x0) {
    return <p className="text-gray-500 text-center py-4">No data to chart yet.</p>
  }

  const maxV = Math.max(1, ...series.flatMap((s) => s.pts.map((p) => p.v)))

  const W = 700
  const H = 320
  const padL = 64
  const padR = 20
  const padT = 20
  const padB = 34

  const sx = (t) => padL + ((t - x0) / (x1 - x0)) * (W - padL - padR)
  const sy = (v) => H - padB - (v / maxV) * (H - padT - padB)

  const spanHours = (x1 - x0) / 36e5
  const fmtTime = (t) =>
    spanHours < 48
      ? new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : new Date(t).toLocaleDateString([], { month: 'short', day: 'numeric' })

  const fmtVal = (v) => (mode === 'money' ? formatGp(v) : Math.round(v).toLocaleString())

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => x0 + f * (x1 - x0))

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} style={{ minWidth: 600, width: '100%' }}>
        {[0, 0.25, 0.5, 0.75, 1].map((f) => {
          const y = sy(f * maxV)
          return (
            <line key={f} x1={padL} x2={W - padR} y1={y} y2={y} stroke="#224b6d" strokeWidth="1" />
          )
        })}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={sx(t)} x2={sx(t)} y1={H - padB} y2={H - padB + 5} stroke="#224b6d" />
            <text x={sx(t)} y={H - padB + 18} fill="#6b7280" fontSize="10" textAnchor="middle">
              {fmtTime(t)}
            </text>
          </g>
        ))}
        {[0, 0.5, 1].map((f) => (
          <text key={f} x={padL - 8} y={sy(f * maxV) + 3} fill="#6b7280" fontSize="10" textAnchor="end">
            {fmtVal(f * maxV)}
          </text>
        ))}
        {series.map((s) => (
          <polyline
            key={s.name}
            points={s.pts.map((p) => `${sx(p.t)},${sy(p.v)}`).join(' ')}
            fill="none"
            stroke={s.color}
            strokeWidth="2.5"
          />
        ))}
        <g transform={`translate(${padL}, ${padT})`}>
          {series.map((s, i) => (
            <text key={s.name} x={i * 100} y={0} fill={s.color} fontSize="11">
              — {s.name}
            </text>
          ))}
        </g>
      </svg>
    </div>
  )
}
