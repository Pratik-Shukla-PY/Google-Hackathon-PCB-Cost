import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Play, Plus, Trash2, Edit2, Check, X, Filter, Info, Volume2 } from "lucide-react"
import { API_BASE_URL, getImageUrl } from "../config"

const CLASS_COLORS = {
  resistor: { border: "border-rose-500", bg: "bg-rose-500/15", text: "text-rose-700", badge: "bg-rose-50 border-rose-200 text-rose-700" },
  capacitor: { border: "border-sky-500", bg: "bg-sky-500/15", text: "text-sky-700", badge: "bg-sky-50 border-sky-200 text-sky-700" },
  inductor: { border: "border-indigo-500", bg: "bg-indigo-500/15", text: "text-indigo-700", badge: "bg-indigo-50 border-indigo-200 text-indigo-700" },
  integrated_circuit: { border: "border-emerald-600", bg: "bg-emerald-600/15", text: "text-emerald-800", badge: "bg-emerald-50 border-emerald-200 text-emerald-800" },
  transistor: { border: "border-amber-600", bg: "bg-amber-600/15", text: "text-amber-800", badge: "bg-amber-50 border-amber-200 text-amber-800" },
  diode: { border: "border-yellow-600", bg: "bg-yellow-600/15", text: "text-yellow-800", badge: "bg-yellow-50 border-yellow-200 text-yellow-800" },
  led: { border: "border-teal-500", bg: "bg-teal-500/15", text: "text-teal-700", badge: "bg-teal-50 border-teal-200 text-teal-700" },
  connector: { border: "border-purple-500", bg: "bg-purple-500/15", text: "text-purple-700", badge: "bg-purple-50 border-purple-200 text-purple-700" },
  crystal: { border: "border-fuchsia-500", bg: "bg-fuchsia-500/15", text: "text-fuchsia-700", badge: "bg-fuchsia-50 border-fuchsia-200 text-fuchsia-700" },
  default: { border: "border-slate-400", bg: "bg-slate-400/15", text: "text-slate-700", badge: "bg-slate-50 border-slate-200 text-slate-700" }
}

const CLASS_OPTIONS = [
  { value: "resistor", label: "Resistor" },
  { value: "capacitor", label: "Capacitor" },
  { value: "inductor", label: "Inductor" },
  { value: "integrated_circuit", label: "Integrated Circuit" },
  { value: "transistor", label: "Transistor" },
  { value: "diode", label: "Diode" },
  { value: "led", label: "LED" },
  { value: "connector", label: "Connector" },
  { value: "crystal", label: "Crystal/Oscillator" },
  { value: "switch", label: "Switch" },
  { value: "fuse", label: "Fuse" },
  { value: "test_point", label: "Test Point" },
  { value: "ferrite_bead", label: "Ferrite Bead" },
  { value: "resistor_network", label: "Resistor Network" },
  { value: "transformer", label: "Transformer" }
]

export default function Review() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  // Data State
  const [project, setProject] = useState(null)
  const [components, setComponents] = useState([])
  const [loading, setLoading] = useState(true)
  const [detecting, setDetecting] = useState(false)
  const [error, setError] = useState("")
  
  // Interactive UI State
  const [hoveredId, setHoveredId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [filterLowConfidence, setFilterLowConfidence] = useState(false)
  const [buildVolume, setBuildVolume] = useState(1000)
  const [renderedDim, setRenderedDim] = useState({ w: 0, h: 0 })
  
  // Inline edit state
  const [editForm, setEditForm] = useState({})
  
  // Manual adding state
  const [isAdding, setIsAdding] = useState(false)
  const [newBoxStart, setNewBoxStart] = useState(null)
  const [newBox, setNewBox] = useState(null) // { x, y, w, h } in CSS pixels
  const [showAddForm, setShowAddForm] = useState(false)
  const [addForm, setAddForm] = useState({
    designator: "",
    component_class: "resistor",
    marking_text: "",
    visual_notes: "",
    confidence: "high"
  })
  
  const imgRef = useRef(null)
  const tableContainerRef = useRef(null)
  const rowRefs = useRef({})

  useEffect(() => {
    fetchProjectAndComponents()
  }, [id])

  const fetchProjectAndComponents = async () => {
    try {
      const projResp = await fetch(`${API_BASE_URL}/api/projects/${id}`)
      if (!projResp.ok) throw new Error("Failed to load project details.")
      const projData = await projResp.json()
      setProject(projData)
      setBuildVolume(projData.build_volume)
      
      const compResp = await fetch(`${API_BASE_URL}/api/projects/${id}/components`)
      if (!compResp.ok) throw new Error("Failed to load components.")
      const compData = await compResp.json()
      
      if (compData.length === 0) {
        // Automatically trigger detection pipeline if no components exist
        await runDetection(projData.id)
      } else {
        setComponents(compData)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const runDetection = async (projId) => {
    setDetecting(true)
    setError("")
    try {
      const resp = await fetch(`${API_BASE_URL}/api/projects/${projId}/detect`, {
        method: "POST"
      })
      if (!resp.ok) throw new Error("Detection pipeline failed.")
      const data = await resp.json()
      setComponents(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setDetecting(false)
    }
  }

  const handleImageLoad = () => {
    if (imgRef.current) {
      const rect = imgRef.current.getBoundingClientRect()
      setRenderedDim({ w: rect.width, h: rect.height })
    }
  }

  // Sync dimensions on resize
  useEffect(() => {
    const handleResize = () => {
      if (imgRef.current) {
        const rect = imgRef.current.getBoundingClientRect()
        setRenderedDim({ w: rect.width, h: rect.height })
      }
    }
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [components])

  const getClassColor = (cls) => {
    return CLASS_COLORS[cls] || CLASS_COLORS.default
  }

  // Hover sync
  const handleBoxHover = (id) => {
    setHoveredId(id)
    if (id && rowRefs.current[id]) {
      rowRefs.current[id].scrollIntoView({
        behavior: "smooth",
        block: "nearest"
      })
    }
  }

  // Inline edits
  const startEdit = (comp) => {
    setEditingId(comp.id)
    setEditForm({ ...comp })
  }

  const handleEditChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }))
  }

  const saveEdit = async (compId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}/components/${compId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm)
      })
      if (!response.ok) throw new Error("Failed to save changes.")
      
      setComponents(prev => prev.map(c => c.id === compId ? { ...c, ...editForm } : c))
      setEditingId(null)
    } catch (err) {
      alert(err.message)
    }
  }

  // Component deletion
  const handleDelete = async (compId) => {
    if (!window.confirm("Are you sure you want to delete this component detection?")) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}/components/${compId}`, {
        method: "DELETE"
      })
      if (!response.ok) throw new Error("Failed to delete component.")
      setComponents(prev => prev.filter(c => c.id !== compId))
    } catch (err) {
      alert(err.message)
    }
  }

  // Draw manual box handlers
  const handleMouseDown = (e) => {
    if (!isAdding || !imgRef.current) return
    const rect = imgRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    setNewBoxStart({ x, y })
    setNewBox({ x, y, w: 0, h: 0 })
    setShowAddForm(false)
  }

  const handleMouseMove = (e) => {
    if (!isAdding || !newBoxStart || !imgRef.current) return
    const rect = imgRef.current.getBoundingClientRect()
    let x = e.clientX - rect.left
    let y = e.clientY - rect.top
    x = Math.max(0, Math.min(x, rect.width))
    y = Math.max(0, Math.min(y, rect.height))
    
    setNewBox({
      x: x < newBoxStart.x ? x : newBoxStart.x,
      y: y < newBoxStart.y ? y : newBoxStart.y,
      w: Math.abs(x - newBoxStart.x),
      h: Math.abs(y - newBoxStart.y)
    })
  }

  const handleMouseUp = () => {
    if (!isAdding || !newBox) return
    setNewBoxStart(null)
    if (newBox.w > 5 && newBox.h > 5) {
      setShowAddForm(true)
    } else {
      setNewBox(null)
    }
  }

  const handleAddSubmit = async () => {
    if (!project || !newBox) return
    
    // Map CSS box to global native pixel coordinates
    const scaleX = project.width / renderedDim.w
    const scaleY = project.height / renderedDim.h
    
    const globalBbox = {
      xmin: newBox.x * scaleX,
      ymin: newBox.y * scaleY,
      xmax: (newBox.x + newBox.w) * scaleX,
      ymax: (newBox.y + newBox.h) * scaleY
    }
    
    const payload = {
      ...addForm,
      bbox: globalBbox,
      manually_added: true,
      is_deleted: false
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}/components`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      if (!response.ok) throw new Error("Failed to add component.")
      const addedComp = await response.json()
      
      setComponents(prev => [...prev, addedComp])
      
      // Reset State
      setIsAdding(false)
      setNewBox(null)
      setShowAddForm(false)
      setAddForm({
        designator: "",
        component_class: "resistor",
        marking_text: "",
        visual_notes: "",
        confidence: "high"
      })
    } catch (err) {
      alert(err.message)
    }
  }

  // Cost BOM generator submit
  const handleProceedToCost = async () => {
    try {
      // Update build volume on project before moving to output screen
      await fetch(`${API_BASE_URL}/api/projects/${id}/volume?volume=${buildVolume}`, {
        method: "POST"
      })
      
      navigate(`/output/${id}`)
    } catch (err) {
      console.error(err)
      navigate(`/output/${id}`)
    }
  }

  // Filtering
  const filteredComponents = components.filter(c => {
    if (filterLowConfidence) {
      return c.confidence.toLowerCase() === "low" || c.confidence.toLowerCase() === "medium"
    }
    return true
  })

  if (loading || detecting) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 font-mono">
        <div className="w-12 h-12 border-4 border-slate-300 border-t-slate-800 rounded-full animate-spin mb-4"></div>
        <div>{detecting ? "Running vision extraction & deduplication..." : "Loading project components..."}</div>
      </div>
    )
  }

  if (error && components.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-600 font-mono mb-4">Error: {error}</div>
        <button 
          onClick={fetchProjectAndComponents}
          className="px-4 py-2 bg-slate-800 text-white rounded text-sm hover:bg-slate-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col md:grid md:grid-cols-12 overflow-hidden h-[calc(100vh-65px)]">
      {/* LEFT: Image Canvas (7 cols) */}
      <div className="md:col-span-7 bg-slate-100 border-r border-slate-200 flex flex-col justify-between overflow-auto p-4 relative select-none">
        
        {/* Draw Instructions overlay */}
        <div className="absolute top-6 left-6 z-10 bg-slate-900/90 text-white text-xs px-3 py-2 rounded font-mono shadow">
          {isAdding ? (
            <span className="text-amber-300 font-semibold animate-pulse">
              [DRAWING MODE] Click and drag on the image to locate the component.
            </span>
          ) : (
            <span>Double click a bounding box or select a row in table to inspect.</span>
          )}
        </div>

        {/* Action strip */}
        <div className="absolute top-6 right-6 z-10 flex gap-2">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className={`px-3 py-1.5 rounded text-xs font-mono font-bold shadow flex items-center gap-1.5 cursor-pointer ${
              isAdding ? "bg-amber-600 text-white hover:bg-amber-700" : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
            }`}
          >
            <Plus className="w-4 h-4" />
            {isAdding ? "Cancel Drawing" : "Add Missed Component"}
          </button>
          
          <button
            onClick={() => runDetection(project.id)}
            className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded text-xs font-mono font-bold shadow"
          >
            Re-run Detection
          </button>
        </div>

        <div className="flex-1 flex items-center justify-center min-h-[400px] py-8">
          {/* Interactive BBox Overlay Wrapper */}
          <div
            className="relative cursor-crosshair border border-slate-300 shadow-sm"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <img
              ref={imgRef}
              src={getImageUrl(project.imageUrl)}
              alt="Board Workspace"
              className="max-h-[75vh] max-w-full object-contain pointer-events-none"
              onLoad={handleImageLoad}
            />

            {/* Rendered BBoxes */}
            {renderedDim.w > 0 && components.map(comp => {
              const bbox = comp.bbox
              const scaleX = renderedDim.w / project.width
              const scaleY = renderedDim.h / project.height
              
              const xmin = bbox.xmin * scaleX
              const ymin = bbox.ymin * scaleY
              const w = (bbox.xmax - bbox.xmin) * scaleX
              const h = (bbox.ymax - bbox.ymin) * scaleY
              
              const isHovered = hoveredId === comp.id
              const isEditing = editingId === comp.id
              const clsConfig = getClassColor(comp.component_class)
              
              return (
                <div
                  key={comp.id}
                  onMouseEnter={() => setHoveredId(comp.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`absolute border-2 transition-all ${clsConfig.border} ${clsConfig.bg} ${
                    isHovered ? "ring-2 ring-blue-600 ring-offset-1 z-20 scale-[1.02]" : "z-10"
                  } ${isEditing ? "border-amber-600 bg-amber-500/10 z-30" : ""}`}
                  style={{
                    left: `${xmin}px`,
                    top: `${ymin}px`,
                    width: `${w}px`,
                    height: `${h}px`
                  }}
                >
                  {/* BBox Label */}
                  <span className={`absolute -top-5 left-0 px-1 py-0.5 text-[9px] font-mono font-bold rounded text-white ${
                    comp.confidence.toLowerCase() === "low" ? "bg-red-500" : "bg-slate-800"
                  }`}>
                    {comp.designator || "Anon"}
                  </span>
                </div>
              )
            })}

            {/* Drawing box overlay */}
            {isAdding && newBox && (
              <div
                className="absolute border-2 border-dashed border-amber-600 bg-amber-100/20 z-40 pointer-events-none"
                style={{
                  left: `${newBox.x}px`,
                  top: `${newBox.y}px`,
                  width: `${newBox.w}px`,
                  height: `${newBox.h}px`
                }}
              />
            )}
          </div>
        </div>

        {/* Add Component Form Modal Overlay */}
        {showAddForm && newBox && (
          <div className="absolute inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white border border-slate-200 rounded p-6 max-w-sm w-full shadow-lg">
              <h3 className="font-mono font-bold text-slate-800 text-sm mb-4">Add Manual Component</h3>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-[10px] font-mono font-bold text-slate-500 mb-1">Designator</label>
                  <input
                    type="text"
                    value={addForm.designator}
                    onChange={(e) => setAddForm(prev => ({ ...prev, designator: e.target.value }))}
                    placeholder="e.g. R20, C15"
                    className="w-full bg-slate-50 border border-slate-300 rounded px-2 py-1.5 text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono font-bold text-slate-500 mb-1">Component Class</label>
                  <select
                    value={addForm.component_class}
                    onChange={(e) => setAddForm(prev => ({ ...prev, component_class: e.target.value }))}
                    className="w-full bg-slate-50 border border-slate-300 rounded px-2 py-1.5 text-xs"
                  >
                    {CLASS_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono font-bold text-slate-500 mb-1">Marking Text</label>
                  <input
                    type="text"
                    value={addForm.marking_text}
                    onChange={(e) => setAddForm(prev => ({ ...prev, marking_text: e.target.value }))}
                    placeholder="Body text or code"
                    className="w-full bg-slate-50 border border-slate-300 rounded px-2 py-1.5 text-xs"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono font-bold text-slate-500 mb-1">Visual Notes</label>
                  <input
                    type="text"
                    value={addForm.visual_notes}
                    onChange={(e) => setAddForm(prev => ({ ...prev, visual_notes: e.target.value }))}
                    placeholder="e.g. black chip, cylinder"
                    className="w-full bg-slate-50 border border-slate-300 rounded px-2 py-1.5 text-xs"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={handleAddSubmit}
                  className="flex-1 bg-slate-800 text-white py-2 rounded text-xs font-bold hover:bg-slate-700 cursor-pointer"
                >
                  Save Component
                </button>
                <button
                  onClick={() => {
                    setNewBox(null)
                    setShowAddForm(false)
                  }}
                  className="flex-1 bg-slate-100 border border-slate-300 text-slate-700 py-2 rounded text-xs font-bold hover:bg-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT: Component Table List (5 cols) */}
      <div className="md:col-span-5 flex flex-col overflow-hidden bg-white">
        
        {/* Table Controls */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <span className="text-xs font-mono font-bold text-slate-600">Filters & Parameters</span>
          </div>
          
          <label className="flex items-center gap-2 text-xs font-mono text-slate-600 select-none cursor-pointer">
            <input
              type="checkbox"
              checked={filterLowConfidence}
              onChange={(e) => setFilterLowConfidence(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Show Only Low/Med Confidence
          </label>
        </div>

        {/* Component Table Scroll Area */}
        <div ref={tableContainerRef} className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <th className="px-4 py-3">Designator</th>
                <th className="px-3 py-3">Class</th>
                <th className="px-3 py-3">Package / Size</th>
                <th className="px-3 py-3">Marking</th>
                <th className="px-3 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredComponents.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-xs text-slate-400 font-mono">
                    No components found matching filters.
                  </td>
                </tr>
              ) : (
                filteredComponents.map(comp => {
                  const isHovered = hoveredId === comp.id
                  const isEditing = editingId === comp.id
                  const clsConfig = getClassColor(comp.component_class)
                  
                  return (
                    <tr
                      key={comp.id}
                      ref={el => rowRefs.current[comp.id] = el}
                      onMouseEnter={() => handleBoxHover(comp.id)}
                      onMouseLeave={() => handleBoxHover(null)}
                      className={`text-xs transition-colors ${
                        isHovered ? "bg-blue-50/40" : ""
                      } ${isEditing ? "bg-amber-50/30" : ""}`}
                    >
                      {/* Designator */}
                      <td className="px-4 py-3 font-mono font-medium">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.designator || ""}
                            onChange={(e) => handleEditChange("designator", e.target.value)}
                            className="bg-white border border-slate-300 rounded px-1.5 py-0.5 w-16 font-mono text-xs focus:outline-none focus:border-slate-400"
                          />
                        ) : (
                          comp.designator || <span className="text-slate-400 font-normal italic">Unmarked</span>
                        )}
                      </td>

                      {/* Class */}
                      <td className="px-3 py-3">
                        {isEditing ? (
                          <select
                            value={editForm.component_class}
                            onChange={(e) => handleEditChange("component_class", e.target.value)}
                            className="bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs focus:outline-none"
                          >
                            {CLASS_OPTIONS.map(opt => (
                              <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                          </select>
                        ) : (
                          <span className={`px-2 py-0.5 border text-[10px] font-mono font-medium rounded ${clsConfig.badge}`}>
                            {comp.component_class.replace("_", " ")}
                          </span>
                        )}
                      </td>

                      {/* Package / Size */}
                      <td className="px-3 py-3 font-mono text-[11px] text-slate-600">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.package || ""}
                            onChange={(e) => handleEditChange("package", e.target.value)}
                            className="bg-white border border-slate-300 rounded px-1.5 py-0.5 w-24 font-mono text-xs focus:outline-none focus:border-slate-400"
                          />
                        ) : (
                          <div>
                            <div>{comp.package || "Unknown"}</div>
                            {comp.measured_width && (
                              <div className="text-[9px] text-slate-400">
                                {comp.measured_width.toFixed(2)}x{comp.measured_height.toFixed(2)}mm
                              </div>
                            )}
                          </div>
                        )}
                      </td>

                      {/* Marking */}
                      <td className="px-3 py-3 font-mono text-slate-500">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.marking_text || ""}
                            onChange={(e) => handleEditChange("marking_text", e.target.value)}
                            className="bg-white border border-slate-300 rounded px-1.5 py-0.5 w-20 text-xs focus:outline-none focus:border-slate-400"
                          />
                        ) : (
                          comp.marking_text || <span className="text-slate-300 font-normal italic">&mdash;</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-3 py-3 text-right">
                        <div className="flex justify-end gap-1.5">
                          {isEditing ? (
                            <>
                              <button
                                onClick={() => saveEdit(comp.id)}
                                className="p-1 hover:bg-slate-100 rounded text-green-700 cursor-pointer"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="p-1 hover:bg-slate-100 rounded text-slate-500 cursor-pointer"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => startEdit(comp)}
                                className="p-1 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-800 cursor-pointer"
                                title="Edit component"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDelete(comp.id)}
                                className="p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-red-600 cursor-pointer"
                                title="Delete component"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer actions: build volume and pricing button */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
              <Volume2 className="w-4 h-4" />
              <span>Annual Build Volume:</span>
            </div>
            
            <input
              type="number"
              value={buildVolume}
              onChange={(e) => setBuildVolume(parseInt(e.target.value) || 0)}
              className="w-24 bg-white border border-slate-300 rounded px-2 py-1 text-xs font-mono text-right focus:outline-none focus:border-slate-400"
            />
          </div>

          <button
            onClick={handleProceedToCost}
            className="w-full bg-slate-800 text-white py-3 rounded text-sm font-medium hover:bg-slate-700 active:bg-slate-900 transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <Play className="w-4 h-4 fill-white text-white" />
            Generate Costed BOM
          </button>
        </div>
      </div>
    </div>
  )
}
