import { useEffect, useMemo, useState } from 'react'
import { useEvent } from '../context/EventContext.jsx'
import { getBosses, getDrops, getBossImages } from '../api.js'
import { Loading, ErrorBox, Empty } from '../components/Status.jsx'
import { formatGp, formatNumber, normName } from '../lib/moneygrab.js'

export default function Bosses() {
  const { selectedEventId } = useEvent()
  const [bosses, setBosses] = useState([])
  const [drops, setDrops] = useState([])
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    Promise.all([getBosses(selectedEventId), getDrops(selectedEventId), getBossImages()])
      .then(([b, d, i]) => {
        if (!active) return
        setBosses(b)
        setDrops(d)
        setImages(i)
      })
      .catch((e) => active && setError(e.message || String(e)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [selectedEventId])

  const imageByName = useMemo(() => {
    const map = {}
    images.forEach((i) => (map[normName(i.boss_name)] = i.image_url))
    return map
  }, [images])

  const dropsByBoss = useMemo(() => {
    const map = {}
    drops.forEach((d) => {
      const key = d.boss_name || 'Other'
      if (!map[key]) map[key] = []
      map[key].push(d)
    })
    return map
  }, [drops])

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  const bossOrder = Array.from(
    new Set([...bosses.map((b) => b.boss_name), ...Object.keys(dropsByBoss)]),
  )

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-[#00a3d1]">Bosses & Drops</h1>

      {bossOrder.length === 0 ? (
        <Empty message="No bosses or drops configured for this event." />
      ) : (
        bossOrder.map((bossName) => {
          const boss = bosses.find((b) => b.boss_name === bossName)
          const items = dropsByBoss[bossName] ?? []
          const imageUrl = imageByName[normName(bossName)]
          return (
            <div key={bossName} className="bg-[#1a364d] p-6 rounded-lg shadow-md">
              <div className="flex items-center gap-3 mb-4">
                {imageUrl && (
                  <img
                    src={imageUrl}
                    alt={bossName}
                    className="w-10 h-10 rounded object-cover bg-[#122a3d]"
                  />
                )}
                <h2 className="text-2xl font-bold text-[#00a3d1]">{bossName}</h2>
              </div>

              {items.length === 0 ? (
                <p className="text-gray-400 text-sm">No drops configured for this boss.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm bg-[#122a3d]">
                    <thead>
                      <tr className="text-left text-[#94a3b8] border-b border-[#224b6d]">
                        <th className="px-4 py-3">Drop</th>
                        <th className="px-4 py-3 text-right">Points</th>
                        <th className="px-4 py-3 text-right">GE Value</th>
                        <th className="px-4 py-3 text-right">GE Low</th>
                        <th className="px-4 py-3 text-right">GE High</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((d) => (
                        <tr
                          key={d.id}
                          className="border-b border-[#224b6d] hover:bg-[#224b6d]/40"
                        >
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
                          <td className="px-4 py-3 text-right text-yellow-400 font-bold">
                            {d.point_value}
                          </td>
                          <td className="px-4 py-3 text-right text-emerald-400 font-bold">
                            {d.ge_value != null ? formatGp(d.ge_value) : '—'}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-400">
                            {d.ge_low != null ? formatNumber(d.ge_low) : '—'}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-400">
                            {d.ge_high != null ? formatNumber(d.ge_high) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}
