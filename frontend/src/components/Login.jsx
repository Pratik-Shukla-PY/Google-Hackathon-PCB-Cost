import { useNavigate } from "react-router-dom"
import { useState } from "react"
import { API_BASE_URL } from "../config"

export default function Login() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const handleSignIn = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      })
      if (response.ok) {
        navigate("/upload")
      } else {
        console.error("Authentication failed")
      }
    } catch (err) {
      console.error("Failed to connect to backend:", err)
      // Fallback for development if backend isn't running yet
      navigate("/upload")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-[#fcfcfc] px-4">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded p-8 shadow-sm">
        <div className="text-center mb-8">
          <div className="inline-block px-3 py-1 bg-slate-100 border border-slate-200 text-xs font-mono font-medium rounded text-slate-600 mb-4">
            Competitor Analysis Tool
          </div>
          <h2 className="text-2xl font-bold font-mono text-slate-800 tracking-tight">
            PCB Cost BOM Generator
          </h2>
          <p className="text-sm text-slate-500 mt-2">
            Extract component packages, identifications and pricing from populated board photographs.
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-slate-300 rounded font-medium text-sm text-slate-700 hover:bg-slate-50 active:bg-slate-100 transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            {loading ? "Authenticating..." : "Sign in with Google"}
          </button>
        </div>

        <div className="mt-8 border-t border-slate-100 pt-6 text-center text-xs text-slate-400">
          Restricted access. Internal costing teams only.
        </div>
      </div>
    </div>
  )
}
