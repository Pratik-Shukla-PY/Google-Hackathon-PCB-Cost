import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { FileSpreadsheet, ArrowLeft, ExternalLink, HelpCircle, ShieldAlert, Award } from "lucide-react"
import { API_BASE_URL } from "../config"

export default function Output() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchCostedBOM()
  }, [id])

  const fetchCostedBOM = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}/cost`)
      if (!response.ok) {
        throw new Error("Failed to calculate costing.")
      }
      const bomData = await response.json()
      setData(bomData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExportExcel = () => {
    // Directly trigger file download from backend route
    window.open(`${API_BASE_URL}/api/projects/${id}/export`, "_blank")
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 font-mono">
        <div className="w-12 h-12 border-4 border-slate-300 border-t-slate-800 rounded-full animate-spin mb-4"></div>
        <div>Calculating sourcing lookups & quantity breaks...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-600 font-mono mb-4">Error: {error}</div>
        <button 
          onClick={fetchCostedBOM}
          className="px-4 py-2 bg-slate-800 text-white rounded text-sm hover:bg-slate-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const { summary, rows } = data

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 flex flex-col gap-6">
      
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(`/review/${id}`)}
          className="flex items-center gap-2 text-xs font-mono font-bold text-slate-600 hover:text-slate-900 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Component Review
        </button>

        <button
          onClick={handleExportExcel}
          className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2.5 rounded text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer shadow-sm"
        >
          <FileSpreadsheet className="w-4 h-4" />
          Download Excel BOM
        </button>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded p-4 shadow-sm">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">Total Board Cost</div>
          <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
            ${summary.board_cost.toFixed(3)}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-mono">at selected volume</div>
        </div>

        <div className="bg-white border border-slate-200 rounded p-4 shadow-sm">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">Unique Line Items</div>
          <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
            {summary.total_line_items}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-mono">BOM groups</div>
        </div>

        <div className="bg-white border border-slate-200 rounded p-4 shadow-sm">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">Total Component Count</div>
          <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
            {summary.total_components}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-mono">visible on board</div>
        </div>

        <div className="bg-amber-50/50 border border-amber-200 rounded p-4 shadow-sm">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-600">Generic Assumptions</div>
          <div className="text-2xl font-bold font-mono text-amber-800 mt-1">
            {summary.generic_costed_count}
          </div>
          <div className="text-[10px] text-amber-600 mt-1 font-mono">unmarked/generic rows</div>
        </div>
      </div>

      {/* Costed BOM Table card */}
      <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <h2 className="text-sm font-bold font-mono text-slate-700">Costed Bill of Materials</h2>
          <span className="text-[10px] px-2 py-0.5 bg-slate-200 text-slate-600 font-mono rounded">
            Currency: USD ($)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[10px] font-mono font-bold uppercase text-slate-500 tracking-wider">
                <th className="px-4 py-3 text-center">Line</th>
                <th className="px-3 py-3">Class</th>
                <th className="px-3 py-3">Designators</th>
                <th className="px-3 py-3 text-center">Qty</th>
                <th className="px-3 py-3">Package</th>
                <th className="px-4 py-3">Manufacturer Part No</th>
                <th className="px-3 py-3">Distributor</th>
                <th className="px-3 py-3 text-center">Basis</th>
                <th className="px-3 py-3 text-right">Unit Price</th>
                <th className="px-4 py-3 text-right">Ext Cost</th>
                <th className="px-4 py-3 text-center">Sourcing</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {rows.map((row) => {
                const isGeneric = row.match_basis.toLowerCase() === "generic"
                return (
                  <tr 
                    key={row.line_number}
                    className={`hover:bg-slate-50/50 ${
                      isGeneric ? "bg-amber-50/20" : ""
                    }`}
                  >
                    <td className="px-4 py-3 text-center text-slate-400">{row.line_number}</td>
                    <td className="px-3 py-3 font-sans text-slate-600 capitalize">
                      {row.component_class.replace("_", " ")}
                    </td>
                    <td className="px-3 py-3 font-sans max-w-[150px] truncate" title={row.designators}>
                      {row.designators}
                    </td>
                    <td className="px-3 py-3 text-center">{row.quantity}</td>
                    <td className="px-3 py-3 text-slate-600">{row.package}</td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{row.part_number}</div>
                      {row.manufacturer && (
                        <div className="text-[10px] text-slate-400 font-sans">{row.manufacturer}</div>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <div className="text-slate-700">{row.distributor}</div>
                      {row.distributor_part_number && (
                        <div className="text-[10px] text-slate-400">{row.distributor_part_number}</div>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={`px-1.5 py-0.5 border text-[9px] font-bold rounded uppercase ${
                        row.match_basis === "identified" 
                          ? "bg-green-50 border-green-200 text-green-700" 
                          : row.match_basis === "equivalent"
                          ? "bg-blue-50 border-blue-200 text-blue-700"
                          : "bg-amber-50 border-amber-200 text-amber-700"
                      }`}>
                        {row.match_basis}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right text-slate-800">${row.unit_price.toFixed(3)}</td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900">${row.extended_cost.toFixed(3)}</td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {row.datasheet_url ? (
                          <a
                            href={row.datasheet_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 hover:bg-slate-100 rounded text-blue-600"
                            title="Datasheet"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        ) : (
                          <span className="text-slate-300">&mdash;</span>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Exclusion disclaimer card */}
      <div className="bg-slate-50 border border-slate-200 rounded p-6">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-slate-600 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wide">
              Teardown Exclusions & Costing Caveat
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              This board cost estimate covers <strong>only the components visible on this side of the board</strong>.
              It specifically excludes the cost of the bare multi-layer PCB, SMT assembly labor, soldering, inspection, testing,
              enclosures, cabling, and any parts shielded under heatsinks or RF cans.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed">
              <strong>Generic Costing Warning:</strong> Ceramic capacitors, resistors, and simple passives lack laser markings.
              For these components, standard commodity specifications (e.g. 10k resistors, 100nF decoupling capacitors) have been assumed
              to provide an order-of-magnitude costing reference.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
