import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getEvents } from '../api.js'

const EventContext = createContext({
  events: [],
  selectedEventId: null,
  setSelectedEventId: () => {},
  selectedEvent: undefined,
  loading: true,
  refreshEvents: async () => [],
})

export function EventProvider({ children }) {
  const [events, setEvents] = useState([])
  const [selectedEventId, setSelectedEventId] = useState(null)
  const [loading, setLoading] = useState(true)

  const refreshEvents = useCallback(async () => {
    const list = await getEvents()
    setEvents(list)
    return list
  }, [])

  useEffect(() => {
    refreshEvents().then((list) => {
      if (list.length > 0) {
        const latest = list.reduce((a, b) =>
          new Date(a.start_date) > new Date(b.start_date) ? a : b,
        )
        setSelectedEventId(latest.id)
      }
      setLoading(false)
    })
  }, [refreshEvents])

  useEffect(() => {
    if (selectedEventId != null) {
      localStorage.setItem('moneygrab_selected_event', String(selectedEventId))
    }
  }, [selectedEventId])

  useEffect(() => {
    const stored = localStorage.getItem('moneygrab_selected_event')
    if (stored && events.length > 0) {
      const id = parseInt(stored, 10)
      if (events.some((e) => e.id === id)) {
        setSelectedEventId(id)
      }
    }
  }, [events])

  const selectedEvent = events.find((e) => e.id === selectedEventId)

  return (
    <EventContext.Provider
      value={{
        events,
        selectedEventId,
        setSelectedEventId,
        selectedEvent,
        loading,
        refreshEvents,
      }}
    >
      {children}
    </EventContext.Provider>
  )
}

export function useEvent() {
  return useContext(EventContext)
}
