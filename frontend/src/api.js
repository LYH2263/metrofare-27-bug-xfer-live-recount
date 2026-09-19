async function readError(r) {
  const t = await r.text()
  try {
    const d = JSON.parse(t).detail
    return typeof d === 'string' ? d : JSON.stringify(d ?? t)
  } catch {
    return t
  }
}
async function send(method, path, body) {
  const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(await readError(r))
  return r.json()
}
export async function getJSON(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(await readError(r))
  return r.json()
}
export function postJSON(path, body) {
  return send('POST', path, body)
}
export function putJSON(path, body) {
  return send('PUT', path, body)
}
