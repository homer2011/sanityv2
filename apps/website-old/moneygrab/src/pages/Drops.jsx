import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useEvent } from '../context/EventContext.jsx'
import { getLinked } from '../api.js'
import { Loading, ErrorBox, Empty } from '../components/Status.jsx'
import { dropGp, formatGp, formatNumber } from '../lib/moneygrab.js'

export default function Drops() {
  const { selectedEventId } = useEvent()
  const [linked, setLinked] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [sortKey, setSortKey] = useState('submission_id')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    getLinked(selectedEventId)
      .then((d) => active && setLinked(d))
      .catch((e) => active && setError(e.message || String(e)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [selectedEventId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return linked
    return linked.filter((d) =>
      [d.submitter, d.team_name, d.item_name, d.boss_name]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(q),
    )
  }, [linked, query])

  const sorted = useMemo(() => {
    const copy = [...filtered]
    copy.sort((a, b) => {
      let av = a[sortKey]
      let bv = b[sortKey]
      if (sortKey === 'money') {
        av = dropGp(a)
        bv = dropGp(b)
      }
      let cmp = 0
      if (typeof av === 'number' && typeof bv === 'number') cmp = av - bv
      else cmp = String(av ?? '').localeCompare(String(bv ?? ''), undefined, { numeric: true })
      return sortDir === 'asc' ? cmp : -cmp
    })
    return copy
  }, [filtered, sortKey, sortDir])

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
    ['submission_id', 'ID'],
    ['reviewedDate', 'Date'],
    ['submitter', 'Submitter'],
    ['team_name', 'Team'],
    ['boss_name', 'Boss'],
    ['item_name', 'Drop'],
    ['point_value', 'Points'],
    ['money', 'GE Value'],
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-[#00a3d1]">Drops</h1>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
        className="w-full p-2 bg-[#1a364d] border border-[#224b6d] rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00a3d1]"
      />

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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Image
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#224b6d]">
            {sorted.map((d) => (
              <tr key={d.link_id} className="hover:bg-[#1a364d] transition-colors">
                <td className="px-4 py-3">{d.submission_id}</td>
                <td className="px-4 py-3">
                  {d.reviewedDate ? new Date(d.reviewedDate).toLocaleDateString() : '—'}
                </td>
                <td className="px-4 py-3">
                  {d.submitter ? (
                    <Link
                      to={`/player/${encodeURIComponent(d.submitter)}`}
                      className="text-[#00a3d1] hover:underline"
                    >
                      {d.submitter}
                    </Link>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-4 py-3">
                  {d.team_id ? (
                    <Link
                      to={`/teams/${d.team_id}`}
                      className="text-[#00a3d1] hover:underline"
                    >
                      {d.team_name}
                    </Link>
                  ) : (
                    <span className="text-red-400 font-bold" title="Submitter not in any team">
                      ⚠ No team
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">{d.boss_name}</td>
                <td className="px-4 py-3">
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
                <td className="px-4 py-3 text-yellow-400 font-bold">
                  {d.point_value}
                </td>
                <td className="px-4 py-3 text-emerald-400 font-bold">
                  {d.ge_value != null
                    ? `${formatGp(d.ge_value)} (${formatNumber(d.ge_value)})`
                    : d.value != null
                      ? formatGp(d.value)
                      : '—'}
                </td>
                <td className="px-4 py-3">
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
        {sorted.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <Empty message="No drops linked yet." />
          </div>
        )}
      </div>
    </div>
  )
}
