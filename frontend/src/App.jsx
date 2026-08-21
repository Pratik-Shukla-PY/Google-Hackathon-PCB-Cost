import { HashRouter, Routes, Route } from "react-router-dom"
import Login from "./components/Login"
import Upload from "./components/Upload"
import Calibrate from "./components/Calibrate"
import Review from "./components/Review"
import Output from "./components/Output"

function App() {
  return (
    <HashRouter>
      <div className="min-h-screen bg-[#fcfcfc] text-[#1e293b] flex flex-col font-sans">
        {/* Top Header */}
        <header className="border-b border-slate-200 bg-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-mono font-bold text-lg tracking-wider text-slate-800">
              PCB Cost BOM Generator
            </span>
            <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-500 rounded border border-slate-200 uppercase tracking-widest font-medium">
              Teardown Tool
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-600">
            <span className="font-mono bg-slate-50 px-2 py-1 rounded border border-slate-100">
              cost_engineer@example.com
            </span>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/calibrate/:id" element={<Calibrate />} />
            <Route path="/review/:id" element={<Review />} />
            <Route path="/output/:id" element={<Output />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}

export default App
