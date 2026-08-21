// Environment-driven API Base URL (configure VITE_API_BASE_URL in Vercel)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export const getImageUrl = (path) => {
  if (!path) return ""
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path
  }
  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`
}
