import { useEffect, useMemo, useState } from 'react'
import { useEvent } from '../context/EventContext.jsx'
import {
  createEvent,
  updateEvent,
  getBosses,
  updateBosses,
  getDrops,
  updateDrops,
  refreshGe,
  lookupGe,
  getTeams,
  getTeamMembers,
  getUsersList,
  addTeam,
  deleteTeam,
  updateTeam,
  importTeams,
  addTeamMember,
  removeTeamMember,
  updateMemberRsn,
  uploadTeamImage,
  getSubmissions,
  linkSubmission,
  unlinkSubmission,
  getBossImages,
  updateBossImage,
  deleteBossImage,
  getBossEhb,
  updateBossEhb,
} from '../api.js'
import { Loading } from '../components/Status.jsx'
import { toSnakeCase, normDrop, formatGp, formatNumber } from '../lib/moneygrab.js'

const BUILDER_PASSWORD = 'moneygrab'
const AUTH_KEY = 'moneygrab_builder_auth'

function Modal({ title, onClose, children }) {
  return (
    <div
      className="fixed inset-0 bg-black/70 flex justify-center items-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#1a364d] p-8 rounded-xl w-full max-w-md max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-xl font-bold text-[#00a3d1]">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function field(label, children) {
  return (
    <label className="block text-sm font-medium text-gray-300 mb-1">
      {label}
      {children}
    </label>
  )
}

const inputCls =
  'mt-1 w-full p-2 bg-[#122a3d] border border-[#224b6d] rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-[#00a3d1]'

function Banner({ type, text }) {
  if (!text) return null
  return (
    <div
      className={`p-4 rounded-md ${
        type === 'error' ? 'bg-red-900/50 text-red-300' : 'bg-green-900/50 text-green-300'
      }`}
    >
      {text}
    </div>
  )
}

export default function Builder() {
  const { selectedEventId, events, refreshEvents } = useEvent()
  const [authed, setAuthed] = useState(
    () => sessionStorage.getItem(AUTH_KEY) === 'true',
  )
  const [pw, setPw] = useState('')
  const [pwError, setPwError] = useState('')
  const [tab, setTab] = useState('event')

  function submitPassword(e) {
    e.preventDefault()
    if (pw === BUILDER_PASSWORD) {
      sessionStorage.setItem(AUTH_KEY, 'true')
      setAuthed(true)
    } else {
      setPwError('Wrong password')
    }
  }

  if (!authed) {
    return (
      <div className="max-w-sm mx-auto mt-20 bg-[#1a364d] p-8 rounded-xl shadow-lg">
        <h2 className="text-2xl font-bold text-[#00a3d1] mb-6 text-center">
          Builder Access
        </h2>
        <form onSubmit={submitPassword}>
          <input
            type="password"
            value={pw}
            autoFocus
            onChange={(e) => setPw(e.target.value)}
            placeholder="Enter password"
            className={inputCls}
          />
          <button
            type="submit"
            className="w-full bg-[#00a3d1] hover:bg-[#0088b0] text-white font-bold py-3 rounded-md transition-colors mt-4"
          >
            Enter
          </button>
        </form>
        {pwError && <p className="mt-4 text-red-400 text-center">{pwError}</p>}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">Builder</h1>
        <button
          onClick={() => {
            sessionStorage.removeItem(AUTH_KEY)
            setAuthed(false)
          }}
          className="text-sm text-gray-400 hover:text-white"
        >
          Log out
        </button>
      </div>

      <div className="flex gap-2 border-b border-[#224b6d] pb-2 flex-wrap">
        {[
          ['event', 'Event'],
          ['bosses', 'Bosses & Drops'],
          ['teams', 'Teams'],
          ['submissions', 'Submissions'],
          ['ehb', 'EHB & Images'],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 rounded-t-md font-bold text-sm transition-colors ${
              tab === key
                ? 'bg-[#00a3d1] text-white'
                : 'bg-[#1a364d] text-gray-300 hover:bg-[#224b6d]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'event' && (
        <EventTab selectedEventId={selectedEventId} events={events} refreshEvents={refreshEvents} />
      )}
      {tab === 'bosses' && <BossesTab selectedEventId={selectedEventId} />}
      {tab === 'teams' && <TeamsTab selectedEventId={selectedEventId} />}
      {tab === 'submissions' && <SubmissionsTab selectedEventId={selectedEventId} />}
      {tab === 'ehb' && <EhbImagesTab selectedEventId={selectedEventId} />}
    </div>
  )
}

// Convert a stored date string to a datetime-local input value (local time).
function toDatetimeLocal(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function fromDatetimeLocal(value) {
  if (!value) return ''
  return value.replace('T', ' ') + ':00'
}

function EventModal({ title, event, onSave, onClose }) {
  const [name, setName] = useState(event?.name ?? '')
  const [start, setStart] = useState(toDatetimeLocal(event?.start_date))
  const [end, setEnd] = useState(toDatetimeLocal(event?.end_date))
  const [womId, setWomId] = useState(event?.wom_id ?? '')
  const [isActive, setIsActive] = useState(Boolean(event?.is_active))

  return (
    <Modal title={title} onClose={onClose}>
      <div className="space-y-3">
        {field('Name', (
          <input value={name} onChange={(e) => setName(e.target.value)} className={inputCls} />
        ))}
        {field('Start Date & Time', (
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} className={inputCls} />
        ))}
        {field('End Date & Time', (
          <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} className={inputCls} />
        ))}
        {event &&
          field('WiseOldMan Competition ID', (
            <input type="number" value={womId} onChange={(e) => setWomId(e.target.value)} className={inputCls} />
          ))}
        {event && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            Active
          </label>
        )}
        <div className="flex gap-3 pt-2">
          <button onClick={onClose} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-700 text-sm">
            Cancel
          </button>
          <button
            onClick={() =>
              onSave({
                name,
                start_date: fromDatetimeLocal(start),
                end_date: fromDatetimeLocal(end),
                wom_id: womId || undefined,
                is_active: isActive,
              })
            }
            className="px-4 py-2 rounded-md bg-[#00a3d1] hover:bg-[#0088b0] text-sm font-bold"
          >
            {event ? 'Save' : 'Create'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ---------- EVENT TAB ----------
function EventTab({ selectedEventId, events, refreshEvents }) {
  const [showNew, setShowNew] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  return (
    <div className="space-y-4">
      <Banner type="error" text={err} />
      <Banner type="success" text={msg} />

      <div className="bg-[#1a364d] p-4 rounded-lg flex gap-3 flex-wrap">
        <button
          onClick={() => setShowNew(true)}
          className="px-3 py-2 rounded-md bg-green-600 hover:bg-green-700 text-sm"
        >
          + New Event
        </button>
        <button
          onClick={() => setShowEdit(true)}
          disabled={!selectedEventId}
          className="px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-sm disabled:opacity-50"
        >
          Edit Selected Event
        </button>
        <span className="text-sm text-gray-400 self-center">
          Select the event to edit from the header dropdown.
        </span>
      </div>

      {showNew && (
        <EventModal
          title="Create New Event"
          onClose={() => setShowNew(false)}
          onSave={async (data) => {
            try {
              await createEvent(data)
              await refreshEvents()
              setMsg('Event created')
              setShowNew(false)
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
        />
      )}

      {showEdit && (
        <EventModal
          title="Edit Event"
          event={events.find((e) => e.id === selectedEventId)}
          onClose={() => setShowEdit(false)}
          onSave={async (data) => {
            try {
              await updateEvent({ event_id: selectedEventId, ...data })
              await refreshEvents()
              setMsg('Event updated')
              setShowEdit(false)
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
        />
      )}
    </div>
  )
}

// ---------- BOSSES & DROPS TAB ----------
function BossesTab({ selectedEventId }) {
  const [bossesText, setBossesText] = useState('')
  const [dropsText, setDropsText] = useState('')
  const [drops, setDrops] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [geBusy, setGeBusy] = useState(false)
  const [lookupName, setLookupName] = useState('')
  const [lookupResult, setLookupResult] = useState(null)
  const [lookupErr, setLookupErr] = useState('')

  async function load() {
    setLoading(true)
    setErr('')
    try {
      const [b, d] = await Promise.all([
        getBosses(selectedEventId),
        getDrops(selectedEventId),
      ])
      setBossesText(
        b
          .sort((x, y) => (x.sort_order ?? 0) - (y.sort_order ?? 0))
          .map((x) => `${x.boss_name}, ${x.wom_metric || ''}`)
          .join('\n'),
      )
      setDropsText(
        d.map((x) => `${x.boss_name}, ${x.item_name}, ${x.point_value}`).join('\n'),
      )
      setDrops(d)
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedEventId) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId])

  function parseBosses() {
    return bossesText
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((line) => {
        const [name, metric] = line.split(',').map((s) => s.trim())
        return { boss_name: name, wom_metric: metric || toSnakeCase(name) }
      })
  }

  function parseDrops() {
    return dropsText
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(',').map((s) => s.trim())
        return {
          boss_name: parts[0] || '',
          item_name: parts[1] || '',
          point_value: Number(parts[2]) || 0,
        }
      })
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-6">
      <Banner type="error" text={err} />
      <Banner type="success" text={msg} />

      <div className="bg-[#1a364d] p-4 rounded-lg">
        <h2 className="text-xl font-bold text-[#00a3d1] mb-2">Bosses</h2>
        <p className="text-xs text-gray-400 mb-2">
          One per line: <code>Boss Name</code> or <code>Boss Name, wom_metric</code>.
          The wom_metric is auto-derived (snake_case) when omitted.
        </p>
        <textarea
          value={bossesText}
          onChange={(e) => setBossesText(e.target.value)}
          rows={4}
          placeholder={'Tombs of Amascut\ntheatre_of_blood'}
          className="w-full p-3 font-mono text-sm bg-[#122a3d] border border-[#224b6d] rounded-md text-white"
        />
        <button
          onClick={async () => {
            try {
              const r = await updateBosses({ event_id: selectedEventId, bosses: parseBosses() })
              setMsg(r.message || 'Bosses saved')
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
          className="mt-2 px-3 py-2 rounded-md bg-green-600 hover:bg-green-700 text-sm"
        >
          Save Bosses
        </button>
      </div>

      <div className="bg-[#1a364d] p-4 rounded-lg">
        <h2 className="text-xl font-bold text-[#00a3d1] mb-2">Drops</h2>
        <p className="text-xs text-gray-400 mb-2">
          One per line: <code>Boss Name, Item Name, Point Value</code>
        </p>
        <textarea
          value={dropsText}
          onChange={(e) => setDropsText(e.target.value)}
          rows={8}
          placeholder={'Tombs of Amascut, Tumeken\'s shadow, 10\nNex, Torva platebody, 8'}
          className="w-full p-3 font-mono text-sm bg-[#122a3d] border border-[#224b6d] rounded-md text-white"
        />
        <button
          onClick={async () => {
            try {
              const r = await updateDrops({ event_id: selectedEventId, drops: parseDrops() })
              setMsg(r.message || 'Drops saved')
              await load()
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
          className="mt-2 px-3 py-2 rounded-md bg-green-600 hover:bg-green-700 text-sm"
        >
          Save Drops
        </button>
      </div>

      <div className="bg-[#1a364d] p-4 rounded-lg">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-xl font-bold text-[#00a3d1]">Grand Exchange Prices</h2>
          <button
            onClick={async () => {
              setGeBusy(true)
              setMsg('')
              try {
                const r = await refreshGe({ event_id: selectedEventId })
                setMsg(
                  r.failed?.length
                    ? `${r.message}. Failed: ${r.failed.join(', ')}`
                    : r.message || 'Refreshed',
                )
                await load()
              } catch (e) {
                setErr(e.message || String(e))
              } finally {
                setGeBusy(false)
              }
            }}
            disabled={geBusy}
            className="px-3 py-2 rounded-md bg-teal-600 hover:bg-teal-700 text-sm disabled:opacity-50"
          >
            {geBusy ? 'Refreshing…' : 'Refresh all GE prices'}
          </button>
        </div>

        <div className="flex gap-2 mt-3 flex-wrap">
          <input
            value={lookupName}
            onChange={(e) => setLookupName(e.target.value)}
            placeholder="Item name to look up"
            className="p-2 bg-[#122a3d] border border-[#224b6d] rounded-md text-white text-sm w-64"
          />
          <button
            onClick={async () => {
              setLookupErr('')
              setLookupResult(null)
              try {
                setLookupResult(await lookupGe({ item_name: lookupName }))
              } catch (e) {
                setLookupErr(e.message || String(e))
              }
            }}
            className="px-3 py-2 rounded-md bg-[#00a3d1] hover:bg-[#0088b0] text-sm"
          >
            Look up
          </button>
        </div>
        {lookupErr && <p className="text-red-400 text-sm mt-2">{lookupErr}</p>}
        {lookupResult && (
          <div className="text-sm text-gray-300 mt-2">
            <span className="text-[#00a3d1]">{lookupResult.name}</span>{' '}
            <span className="text-gray-500">(#{lookupResult.wiki_item_id})</span> — GE:{' '}
            <span className="text-emerald-400">
              {lookupResult.ge_value != null ? formatGp(lookupResult.ge_value) : 'n/a'}
            </span>{' '}
            low {formatNumber(lookupResult.ge_low)} / high {formatNumber(lookupResult.ge_high)}
          </div>
        )}

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm bg-[#122a3d]">
            <thead>
              <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                <th className="px-3 py-2">Boss</th>
                <th className="px-3 py-2">Item</th>
                <th className="px-3 py-2 text-right">Points</th>
                <th className="px-3 py-2 text-right">GE Value</th>
              </tr>
            </thead>
            <tbody>
              {drops.map((d) => (
                <tr key={d.id} className="border-b border-[#224b6d]/50">
                  <td className="px-3 py-2">{d.boss_name}</td>
                  <td className="px-3 py-2">{d.item_name}</td>
                  <td className="px-3 py-2 text-right text-yellow-400">{d.point_value}</td>
                  <td className="px-3 py-2 text-right text-emerald-400">
                    {d.ge_value != null ? formatGp(d.ge_value) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ---------- TEAMS TAB ----------
function TeamsTab({ selectedEventId }) {
  const [teams, setTeams] = useState([])
  const [members, setMembers] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')

  const [importText, setImportText] = useState('')
  const [newName, setNewName] = useState('')
  const [captainId, setCaptainId] = useState('')
  const [cocaptainId, setCocaptainId] = useState('')

  async function load() {
    setLoading(true)
    try {
      const [t, m, u] = await Promise.all([
        getTeams(selectedEventId),
        getTeamMembers(selectedEventId),
        getUsersList(),
      ])
      setTeams(t)
      setMembers(m)
      setUsers(u)
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId])

  const membersByTeam = useMemo(() => {
    const m = {}
    members.forEach((x) => {
      if (!m[x.team_id]) m[x.team_id] = []
      m[x.team_id].push(x)
    })
    return m
  }, [members])

  if (loading) return <Loading />

  return (
    <div className="space-y-6">
      <Banner type="error" text={err} />
      <Banner type="success" text={msg} />

      <div className="bg-[#1a364d] p-4 rounded-lg space-y-2">
        <h2 className="font-bold text-[#00a3d1]">Import Teams</h2>
        <p className="text-xs text-gray-400">
          Format: TeamName, DisplayName, RSN, DisplayName, RSN... (captain first,
          co-captain second)
        </p>
        <textarea
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
          rows={4}
          placeholder="Baldies, Box, box rsn, Homer, homer alt"
          className="w-full p-3 font-mono text-xs bg-[#122a3d] border border-[#224b6d] rounded-md text-white"
        />
        <button
          onClick={async () => {
            try {
              const r = await importTeams({ event_id: selectedEventId, lines: importText })
              setMsg(r.message || 'Imported')
              await load()
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
          className="px-3 py-2 rounded-md bg-purple-600 hover:bg-purple-700 text-sm"
        >
          Import
        </button>
      </div>

      <div className="flex gap-3 flex-wrap items-end">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Team Name"
          className={inputCls + ' max-w-[200px]'}
        />
        <select value={captainId} onChange={(e) => setCaptainId(e.target.value)} className={inputCls + ' max-w-[200px]'}>
          <option value="">Captain *</option>
          {users.map((u) => (
            <option key={u.userId} value={u.userId}>
              {u.displayName}
            </option>
          ))}
        </select>
        <select value={cocaptainId} onChange={(e) => setCocaptainId(e.target.value)} className={inputCls + ' max-w-[200px]'}>
          <option value="">None (Co-Captain)</option>
          {users.map((u) => (
            <option key={u.userId} value={u.userId}>
              {u.displayName}
            </option>
          ))}
        </select>
        <button
          onClick={async () => {
            try {
              await addTeam({
                event_id: selectedEventId,
                name: newName,
                captain_userid: captainId || null,
                cocaptain_userid: cocaptainId || null,
              })
              setNewName('')
              setCaptainId('')
              setCocaptainId('')
              await load()
            } catch (e) {
              setErr(e.message || String(e))
            }
          }}
          disabled={!newName}
          className="px-3 py-2 rounded-md bg-green-600 hover:bg-green-700 text-sm disabled:opacity-50 h-[42px]"
        >
          Add Team
        </button>
      </div>

      {teams.map((team) => {
        const roster = membersByTeam[team.id] ?? []
        const used = new Set(roster.map((m) => m.user_id))
        return (
          <div key={team.id} className="bg-[#1a364d] p-4 rounded-lg space-y-3">
            <div className="flex items-center gap-3 flex-wrap">
              <input
                defaultValue={team.name}
                onBlur={async (e) => {
                  try {
                    await updateTeam({ team_id: team.id, name: e.target.value })
                  } catch (err2) {
                    setErr(err2.message || String(err2))
                  }
                }}
                className="text-xl font-bold text-[#00a3d1] bg-transparent border-b border-[#224b6d] w-40"
              />
              <button
                onClick={async () => {
                  if (confirm('Delete this team?')) {
                    await deleteTeam({ team_id: team.id })
                    await load()
                  }
                }}
                className="text-red-400 hover:underline text-sm"
              >
                Delete Team
              </button>
            </div>

            <div className="flex items-center gap-3">
              {team.image_url ? (
                <img
                  src={team.image_url}
                  alt={team.name}
                  className="w-12 h-12 rounded object-cover bg-[#122a3d]"
                />
              ) : (
                <div className="w-12 h-12 rounded bg-[#122a3d] border border-[#224b6d] flex items-center justify-center text-gray-500 text-[10px]">
                  Logo
                </div>
              )}
              <label className="px-3 py-2 rounded-md bg-[#00a3d1] hover:bg-[#0088b0] text-sm cursor-pointer">
                Upload Logo
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files && e.target.files[0]
                    if (!file) return
                    try {
                      setErr('')
                      setMsg('')
                      await uploadTeamImage(team.id, file)
                      setMsg('Logo uploaded')
                      await load()
                    } catch (err2) {
                      setErr(err2.message || String(err2))
                    } finally {
                      e.target.value = ''
                    }
                  }}
                />
              </label>
            </div>

            <div className="flex gap-3 flex-wrap text-sm">
              <span className="text-gray-400">Capt: {team.captain_name ?? '—'}</span>
              <span className="text-gray-400">CoCapt: {team.cocaptain_name ?? '—'}</span>
            </div>

            <div className="space-y-1">
              {roster.map((m) => (
                <div key={m.user_id} className="flex items-center gap-2 text-sm">
                  <span className="w-40">{m.displayName}</span>
                  <input
                    defaultValue={m.rsn ?? ''}
                    onBlur={async (e) => {
                      try {
                        await updateMemberRsn({
                          team_id: team.id,
                          user_id: m.user_id,
                          rsn: e.target.value,
                        })
                      } catch (err2) {
                        setErr(err2.message || String(err2))
                      }
                    }}
                    placeholder="RSN"
                    className="text-yellow-400 text-xs bg-transparent border-b border-[#224b6d] w-32"
                  />
                  <button
                    onClick={async () => {
                      await removeTeamMember({ team_id: team.id, user_id: m.user_id })
                      await load()
                    }}
                    className="text-red-400 hover:underline text-xs"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            <AddMember
              users={users.filter((u) => !used.has(u.userId))}
              onAdd={async (userId) => {
                await addTeamMember({ team_id: team.id, user_id: userId })
                await load()
              }}
            />
          </div>
        )
      })}
    </div>
  )
}

function AddMember({ users, onAdd }) {
  const [userId, setUserId] = useState('')
  return (
    <div className="flex items-center gap-2 text-sm">
      <select value={userId} onChange={(e) => setUserId(e.target.value)} className={inputCls + ' max-w-[200px]'}>
        <option value="">Add member...</option>
        {users.map((u) => (
          <option key={u.userId} value={u.userId}>
            {u.displayName}
          </option>
        ))}
      </select>
      <button
        onClick={async () => {
          if (userId) {
            await onAdd(userId)
            setUserId('')
          }
        }}
        disabled={!userId}
        className="px-3 py-2 rounded-md bg-[#00a3d1] hover:bg-[#0088b0] disabled:opacity-50"
      >
        + Add
      </button>
    </div>
  )
}

// ---------- SUBMISSIONS TAB ----------
function SubmissionsTab({ selectedEventId }) {
  const [submissions, setSubmissions] = useState([])
  const [drops, setDrops] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function load() {
    setLoading(true)
    try {
      const [s, d] = await Promise.all([
        getSubmissions(selectedEventId),
        getDrops(selectedEventId),
      ])
      setSubmissions(s)
      setDrops(d)
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId])

  function suggestedDropId(submission) {
    const note = normDrop(submission.notes)
    const exact = drops.find((d) => normDrop(d.item_name) === note)
    if (exact) return exact.id
    const partial = drops.find((d) => normDrop(d.item_name).includes(note) || note.includes(normDrop(d.item_name)))
    return partial ? partial.id : ''
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-[#00a3d1]">
        Link Approved Submissions
      </h2>
      <p className="text-sm text-gray-400">
        Approved Discord drops (within the event window) appear below. Link each
        one to a configured drop so it counts toward the leaderboard.
      </p>
      <Banner type="error" text={err} />
      <Banner type="success" text={msg} />

      <div className="bg-[#1a364d] rounded-lg shadow-lg overflow-hidden">
        <table className="w-full text-sm bg-[#122a3d]">
          <thead>
            <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
              <th className="px-3 py-3">ID</th>
              <th className="px-3 py-3">Date</th>
              <th className="px-3 py-3">Submitter</th>
              <th className="px-3 py-3">Drop</th>
              <th className="px-3 py-3">Drop (event)</th>
              <th className="px-3 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map((s) => (
              <SubmissionRow
                key={s.Id}
                submission={s}
                drops={drops}
                suggestion={suggestedDropId(s)}
                onLinked={async (dropId) => {
                  try {
                    const r = await linkSubmission({
                      event_id: selectedEventId,
                      submission_id: s.Id,
                      drop_id: Number(dropId),
                    })
                    setMsg(r.message || 'Linked')
                    await load()
                  } catch (e) {
                    setErr(e.message || String(e))
                  }
                }}
                onUnlinked={async () => {
                  try {
                    const r = await unlinkSubmission({ submission_id: s.Id })
                    setMsg(r.message || 'Unlinked')
                    await load()
                  } catch (e) {
                    setErr(e.message || String(e))
                  }
                }}
              />
            ))}
            {submissions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-gray-500">
                  No approved submissions in the event window.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SubmissionRow({ submission: s, drops, suggestion, onLinked, onUnlinked }) {
  const [dropId, setDropId] = useState(s.linked ? s.drop_id : suggestion)
  const [busy, setBusy] = useState(false)

  return (
    <tr className="border-b border-[#224b6d] hover:bg-[#224b6d]/40 align-top">
      <td className="px-3 py-3">{s.Id}</td>
      <td className="px-3 py-3">
        {s.reviewedDate ? new Date(s.reviewedDate).toLocaleDateString() : '—'}
      </td>
      <td className="px-3 py-3">{s.submitter ?? '—'}</td>
      <td className="px-3 py-3">{s.notes}</td>
      <td className="px-3 py-3">
        <select
          value={dropId ?? ''}
          onChange={(e) => setDropId(e.target.value)}
          className="bg-[#122a3d] border border-[#224b6d] rounded-md p-1 text-white text-xs"
        >
          <option value="">Select drop...</option>
          {drops.map((d) => (
            <option key={d.id} value={d.id}>
              {d.boss_name} — {d.item_name} ({d.point_value} pts)
            </option>
          ))}
        </select>
      </td>
      <td className="px-3 py-3">
        {s.linked ? (
          <span className="flex gap-2 items-center">
            <span className="text-emerald-400 text-xs">Linked</span>
            <button
              onClick={async () => {
                setBusy(true)
                await onUnlinked()
                setBusy(false)
              }}
              disabled={busy}
              className="px-2 py-1 rounded bg-red-600/70 hover:bg-red-600 text-xs disabled:opacity-50"
            >
              Unlink
            </button>
          </span>
        ) : (
          <button
            onClick={async () => {
              if (!dropId) return
              setBusy(true)
              await onLinked(dropId)
              setBusy(false)
            }}
            disabled={!dropId || busy}
            className="px-2 py-1 rounded bg-[#00a3d1] hover:bg-[#0088b0] text-xs disabled:opacity-50"
          >
            Link
          </button>
        )}
      </td>
    </tr>
  )
}

// ---------- EHB & IMAGES TAB ----------
function EhbImagesTab({ selectedEventId }) {
  const [ehbText, setEhbText] = useState('')
  const [ehb, setEhb] = useState([])
  const [images, setImages] = useState([])
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function load() {
    try {
      const [e, i] = await Promise.all([
        getBossEhb(selectedEventId),
        getBossImages(),
      ])
      setEhb(e)
      setEhbText(e.map((x) => `${x.boss}, ${x.ehb}`).join('\n'))
      setImages(i)
    } catch (e2) {
      setErr(e2.message || String(e2))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId])

  async function saveEhb() {
    const list = ehbText
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => {
        const [boss, ehbVal] = l.split(',').map((s) => s.trim())
        return { boss, ehb: Number(ehbVal) || 0 }
      })
    try {
      for (const item of list) {
        await updateBossEhb({ event_id: selectedEventId, boss: item.boss, ehb: item.ehb })
      }
      setMsg('EHB saved')
      await load()
    } catch (e) {
      setErr(e.message || String(e))
    }
  }

  return (
    <div className="space-y-6">
      <Banner type="error" text={err} />
      <Banner type="success" text={msg} />

      <div className="bg-[#1a364d] p-4 rounded-lg">
        <h2 className="text-xl font-bold text-[#00a3d1] mb-2">Boss EHB Rates</h2>
        <p className="text-xs text-gray-400 mb-2">
          One per line: <code>boss, ehb</code> (e.g. <code>Nex, 12.5</code>).
          EHB = kills per hour, used for the individual EHB leaderboard.
        </p>
        <textarea
          value={ehbText}
          onChange={(e) => setEhbText(e.target.value)}
          rows={6}
          placeholder={'Nex, 12.5\nTombs of Amascut, 2.5'}
          className="w-full p-3 font-mono text-sm bg-[#122a3d] border border-[#224b6d] rounded-md text-white"
        />
        <button
          onClick={saveEhb}
          className="mt-2 px-3 py-2 rounded-md bg-green-600 hover:bg-green-700 text-sm"
        >
          Save EHB
        </button>
      </div>

      <BossImages images={images} setImages={setImages} setErr={setErr} setMsg={setMsg} />
    </div>
  )
}

function BossImages({ images, setImages, setErr, setMsg }) {
  const [bossName, setBossName] = useState('')
  const [url, setUrl] = useState('')
  const [editingId, setEditingId] = useState(null)

  async function save() {
    setMsg('')
    setErr('')
    try {
      await updateBossImage(
        editingId
          ? { id: editingId, boss_name: bossName, image_url: url }
          : { boss_name: bossName, image_url: url },
      )
      setMsg('Saved')
      setBossName('')
      setUrl('')
      setEditingId(null)
      setImages(await getBossImages())
    } catch (e) {
      setErr(e.message || String(e))
    }
  }

  return (
    <div className="bg-[#1a364d] p-4 rounded-lg space-y-3">
      <h2 className="text-xl font-bold text-[#00a3d1]">Boss Images</h2>
      <div className="flex gap-2 flex-wrap">
        <input
          value={bossName}
          onChange={(e) => setBossName(e.target.value)}
          placeholder="Boss name"
          className="p-2 bg-[#122a3d] border border-[#224b6d] rounded-md text-white text-sm"
        />
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Image URL"
          className="p-2 bg-[#122a3d] border border-[#224b6d] rounded-md text-white text-sm flex-grow"
        />
        <button
          onClick={save}
          className="px-3 py-2 rounded-md bg-[#00a3d1] hover:bg-[#0088b0] text-sm"
        >
          {editingId ? 'Update' : 'Add'}
        </button>
        {editingId && (
          <button
            onClick={() => {
              setEditingId(null)
              setBossName('')
              setUrl('')
            }}
            className="px-3 py-2 rounded-md bg-gray-600 hover:bg-gray-700 text-sm"
          >
            Cancel
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-60 overflow-y-auto">
        {images.map((b) => (
          <div
            key={b.id}
            className="bg-[#122a3d] p-2 rounded flex items-center gap-2 text-sm"
          >
            <span className="flex-grow truncate">{b.boss_name}</span>
            <button
              onClick={() => {
                setEditingId(b.id)
                setBossName(b.boss_name)
                setUrl(b.image_url ?? '')
              }}
              className="text-[#00a3d1] hover:underline"
            >
              Edit
            </button>
            <button
              onClick={async () => {
                try {
                  await deleteBossImage({ id: b.id })
                  setImages(await getBossImages())
                } catch (e) {
                  setErr(e.message || String(e))
                }
              }}
              className="text-red-400 hover:underline"
            >
              Del
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
