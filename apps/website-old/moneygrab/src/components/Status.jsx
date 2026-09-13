export function Loading() {
  return <div className="py-8 text-center text-[#94a3b8]">Loading…</div>
}

export function ErrorBox({ message }) {
  return (
    <div className="py-8 text-center text-red-400">
      Error: {message}
    </div>
  )
}

export function Empty({ message = 'No data' }) {
  return <div className="py-8 text-center text-[#94a3b8]">{message}</div>
}
