// API client for the Sanity Money Grab backend.
// All money-grab endpoints live under /api/moneygrab on the same origin.

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = await res.json()
      message = body.error || message
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(message)
  }
  return res.json()
}

const get = (path) => request(path)
const post = (path, body) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

// --- Events ---
export const getEvents = () => get('/moneygrab/events')
export const createEvent = (data) => post('/moneygrab/create_event', data)
export const updateEvent = (data) => post('/moneygrab/update_event', data)

// --- Bosses ---
export const getBosses = (eventId) =>
  get(`/moneygrab/bosses${eventId ? `?event_id=${eventId}` : ''}`)
export const updateBosses = (data) => post('/moneygrab/update_bosses', data)

// --- Drops ---
export const getDrops = (eventId) =>
  get(`/moneygrab/drops${eventId ? `?event_id=${eventId}` : ''}`)
export const updateDrops = (data) => post('/moneygrab/update_drops', data)
export const refreshGe = (data) => post('/moneygrab/refresh_ge', data)
export const lookupGe = (data) => post('/moneygrab/lookup_ge', data)

// --- Teams ---
export const getTeams = (eventId) =>
  get(`/moneygrab/teams${eventId ? `?event_id=${eventId}` : ''}`)
export const getTeamMembers = (eventId) =>
  get(`/moneygrab/teammembers${eventId ? `?event_id=${eventId}` : ''}`)
export const addTeam = (data) => post('/moneygrab/add_team', data)
export const updateTeam = (data) => post('/moneygrab/update_team', data)
export const deleteTeam = (data) => post('/moneygrab/delete_team', data)
export const importTeams = (data) => post('/moneygrab/import_teams', data)
export const addTeamMember = (data) => post('/moneygrab/add_team_member', data)
export const removeTeamMember = (data) => post('/moneygrab/remove_team_member', data)
export const updateMemberRsn = (data) => post('/moneygrab/update_member_rsn', data)
export const uploadTeamImage = (teamId, file) => {
  const fd = new FormData()
  fd.append('team_id', teamId)
  fd.append('file', file)
  return request('/moneygrab/upload_team_image', {
    method: 'POST',
    body: fd,
  })
}

// --- Submissions / linking ---
export const getSubmissions = (eventId) =>
  get(`/moneygrab/submissions${eventId ? `?event_id=${eventId}` : ''}`)
export const linkSubmission = (data) => post('/moneygrab/link_submission', data)
export const unlinkSubmission = (data) => post('/moneygrab/unlink_submission', data)
export const getLinked = (eventId) =>
  get(`/moneygrab/linked${eventId ? `?event_id=${eventId}` : ''}`)

// --- Boss images & EHB ---
export const getBossImages = () => get('/moneygrab/boss_images')
export const updateBossImage = (data) => post('/moneygrab/update_boss_image', data)
export const deleteBossImage = (data) => post('/moneygrab/delete_boss_image', data)
export const getBossEhb = (eventId) =>
  get(`/moneygrab/boss_ehb${eventId ? `?event_id=${eventId}` : ''}`)
export const updateBossEhb = (data) => post('/moneygrab/update_boss_ehb', data)
export const deleteBossEhb = (data) => post('/moneygrab/delete_boss_ehb', data)

// --- Shared (reuse existing endpoints) ---
export const getRsnKc = () => get('/getRSNkc')
export const getUsersList = () => get('/users/list')
export const getDiscordProfiles = () => get('/discordProfileUrl')
