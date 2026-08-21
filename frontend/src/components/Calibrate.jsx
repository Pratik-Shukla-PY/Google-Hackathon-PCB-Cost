import { useState, useEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Ruler, AlertTriangle, ArrowRight, RefreshCw, Upload } from "lucide-react"
import { API_BASE_URL, getImageUrl } from "../config"

export default function Calibrate() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  
  // Drawing state
  const [isDrawing, setIsDrawing] = useState(false)
  const [box, setBox] = useState(null) // { x, y, w, h } in rendered CSS pixels
  const [startPos, setStartPos] = useState({ x: 0, y: 0 })
  const [renderedDim, setRenderedDim] = useState({ w: 0, h: 0 })
  
  // Physical measurements inputs
  const [realW, setRealW] = useState("")
  const [realH, setRealH] = useState("")
  
  // Result state
  const [calibResult, setCalibResult] = useState(null)
  const [showSkewWarning, setShowSkewWarning] = useState(false)
  const [saving, setSaving] = useState(false)
  
  const containerRef = useRef(null)
  const imgRef = useRef(null)

  useEffect(() => {
    fetchProject()
  }, [id])

  const fetchProject = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}`)
      if (!response.ok) {
        throw new Error("Failed to load project details.")
      }
      const data = await response.json()
      setProject(data)
      
      // If calibration already exists, populate it
      if (data.reference_box) {
        // We will let the user redraw, but they can see current specs
        setRealW(data.reference_box.real_w.toString())
        setRealH(data.reference_box.real_h.toString())
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleImageLoad = () => {
    if (imgRef.current) {
      const rect = imgRef.current.getBoundingClientRect()
      setRenderedDim({ w: rect.width, h: rect.height })
      
      // If project has existing reference box, map it back to rendered coords
      if (project && project.reference_box) {
        const ref = project.reference_box
        const scaleX = rect.width / project.width
        const scaleY = rect.height / project.height
        setBox({
          x: ref.box_x * scaleX,
          y: ref.box_y * scaleY,
          w: ref.box_w * scaleX,
          h: ref.box_h * scaleY
        })
      }
    }
  }

  // Handle window resizing to keep the box proportional
  useEffect(() => {
    const handleResize = () => {
      if (imgRef.current && project && box) {
        const rect = imgRef.current.getBoundingClientRect()
        // Compute new position based on ratios
        const oldW = renderedDim.w || rect.width
        const oldH = renderedDim.h || rect.height
        const scaleX = rect.width / oldW
        const scaleY = rect.height / oldH
        
        setBox(prev => prev ? {
          x: prev.x * scaleX,
          y: prev.y * scaleY,
          w: prev.w * scaleX,
          h: prev.h * scaleY
        } : null)
        
        setRenderedDim({ w: rect.width, h: rect.height })
      }
    }
    
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [renderedDim, project, box])

  const handleMouseDown = (e) => {
    if (!imgRef.current) return
    const rect = imgRef.current.getBoundingClientRect()
    
    // Coordinates relative to the image element
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    setIsDrawing(true)
    setStartPos({ x, y })
    setBox({ x, y, w: 0, h: 0 })
    setCalibResult(null)
    setShowSkewWarning(false)
  }

  const handleMouseMove = (e) => {
    if (!isDrawing || !imgRef.current) return
    const rect = imgRef.current.getBoundingClientRect()
    
    // Bound movement inside image size
    let x = e.clientX - rect.left
    let y = e.clientY - rect.top
    
    x = Math.max(0, Math.min(x, rect.width))
    y = Math.max(0, Math.min(y, rect.height))
    
    const w = x - startPos.x
    const h = y - startPos.y
    
    setBox({
      x: w < 0 ? x : startPos.x,
      y: h < 0 ? y : startPos.y,
      w: Math.abs(w),
      h: Math.abs(h)
    })
  }

  const handleMouseUp = () => {
    setIsDrawing(false)
    // Avoid tiny boxes from clicks
    if (box && (box.w < 5 || box.h < 5)) {
      setBox(null)
    }
  }

  const handleCalculateScale = async () => {
    if (!box || !realW || !realH || !project) return
    setSaving(true)
    setError("")
    
    // Map rendered box coordinates to image native resolution
    const scaleX = project.width / renderedDim.w
    const scaleY = project.height / renderedDim.h
    
    const nativeBox = {
      box_x: box.x * scaleX,
      box_y: box.y * scaleY,
      box_w: box.w * scaleX,
      box_h: box.h * scaleY,
      real_w: parseFloat(realW),
      real_h: parseFloat(realH)
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${id}/calibrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody(nativeBox)
      })
      
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || "Calibration failed")
      }
      
      setCalibResult(data)
      if (data.is_skewed) {
        setShowSkewWarning(true)
      } else {
        // Automatically proceed if skew is fine
        navigate(`/review/${id}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const jsonBody = (obj) => JSON.stringify(obj)

  if (loading) return <div className="p-8 text-center font-mono">Loading project...</div>
  if (error && !project) return <div className="p-8 text-red-600 font-mono">Error: {error}</div>

  return (
    <div className="flex-1 flex flex-col md:grid md:grid-cols-4 gap-6 p-6">
      {/* Canvas workspace: 3 cols */}
      <div className="md:col-span-3 bg-white border border-slate-200 rounded p-6 shadow-sm flex flex-col items-center justify-center relative min-h-[400px]">
        <h2 className="text-sm font-bold font-mono text-slate-500 absolute top-4 left-6">
          Calibration Workspace &mdash; Draw scale reference box
        </h2>
        
        {/* Draw Area container */}
        <div 
          ref={containerRef}
          className="relative max-w-full max-h-[70vh] cursor-crosshair select-none border border-slate-200 mt-6"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <img
            ref={imgRef}
            src={getImageUrl(project.imageUrl)}
            alt="Board to calibrate"
            className="max-w-full max-h-[70vh] object-contain pointer-events-none"
            onLoad={handleImageLoad}
          />
          
          {/* Overlay Box element */}
          {box && (
            <div
              className="absolute border-2 border-blue-600 bg-blue-100/10 pointer-events-none"
              style={{
                left: `${box.x}px`,
                top: `${box.y}px`,
                width: `${box.w}px`,
                height: `${box.h}px`
              }}
            >
              <div className="absolute -top-6 left-0 bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded font-mono font-medium">
                Ref Box: {Math.round(box.w * (project.width / renderedDim.w))}x{Math.round(box.h * (project.height / renderedDim.h))} px
              </div>
            </div>
          )}
        </div>
        
        <div className="text-xs text-slate-400 mt-4 text-center font-mono">
          Click and drag a box over an object of known dimensions (e.g., the board edges or a dual inline package IC).
        </div>
      </div>

      {/* Control Panel: 1 col */}
      <div className="md:col-span-1 flex flex-col gap-6">
        <div className="bg-white border border-slate-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Ruler className="w-5 h-5 text-slate-700" />
            <h3 className="font-mono font-bold text-slate-800">Scale Calibration</h3>
          </div>

          <p className="text-xs text-slate-400 leading-normal mb-6">
            Draw a rectangle on the board photograph representing a component or outline of known physical dimensions.
          </p>

          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-xs font-mono font-bold text-slate-500 mb-1.5">
                Real Width (mm)
              </label>
              <input
                type="number"
                step="any"
                value={realW}
                onChange={(e) => setRealW(e.target.value)}
                placeholder="e.g. 100"
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-slate-400 font-mono"
              />
            </div>
            
            <div>
              <label className="block text-xs font-mono font-bold text-slate-500 mb-1.5">
                Real Height (mm)
              </label>
              <input
                type="number"
                step="any"
                value={realH}
                onChange={(e) => setRealH(e.target.value)}
                placeholder="e.g. 50"
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-slate-400 font-mono"
              />
            </div>
          </div>

          <button
            onClick={handleCalculateScale}
            disabled={!box || !realW || !realH || saving}
            className="w-full bg-slate-800 text-white py-3 rounded text-sm font-medium hover:bg-slate-700 active:bg-slate-900 transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Calculate Scale"}
          </button>
        </div>

        {/* Skew Warning Block */}
        {showSkewWarning && calibResult && (
          <div className="bg-amber-50 border border-amber-200 rounded p-5 flex flex-col gap-4">
            <div className="flex gap-2 text-amber-800">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h4 className="font-bold text-xs font-mono">Skew Detected (&gt; 5%)</h4>
            </div>
            <p className="text-xs text-amber-700 leading-normal">
              The camera appears skewed. Scale factors differ by <strong className="font-mono">{(calibResult.difference * 100).toFixed(1)}%</strong>:
            </p>
            <div className="bg-white/50 border border-amber-100 rounded p-2 text-[11px] font-mono text-slate-600">
              <div>Scale X: {calibResult.scale_x.toFixed(2)} px/mm</div>
              <div>Scale Y: {calibResult.scale_y.toFixed(2)} px/mm</div>
            </div>
            <p className="text-xs text-amber-700">
              Skewed coordinates distort physical component dimension calculations. You can re-draw, re-upload, or continue anyway.
            </p>
            
            <div className="flex flex-col gap-2 mt-2">
              <button
                onClick={() => navigate(`/review/${id}`)}
                className="w-full bg-amber-600 text-white py-2 rounded text-xs font-bold hover:bg-amber-700 active:bg-amber-800 cursor-pointer flex items-center justify-center gap-1"
              >
                Continue Anyway <ArrowRight className="w-3.5 h-3.5" />
              </button>
              
              <button
                onClick={() => {
                  setBox(null);
                  setCalibResult(null);
                  setShowSkewWarning(false);
                }}
                className="w-full bg-white border border-amber-300 text-amber-800 py-2 rounded text-xs font-bold hover:bg-amber-50 active:bg-amber-100 cursor-pointer"
              >
                Re-draw Box
              </button>
              
              <button
                onClick={() => navigate("/upload")}
                className="w-full bg-white border border-slate-300 text-slate-700 py-2 rounded text-xs font-bold hover:bg-slate-50 cursor-pointer flex items-center justify-center gap-1"
              >
                <Upload className="w-3.5 h-3.5" /> Re-upload Image
              </button>
            </div>
          </div>
        )}

        {/* Display Scale Factor if calibrated and not showing warning */}
        {calibResult && !showSkewWarning && (
          <div className="bg-green-50 border border-green-200 rounded p-4 text-xs font-mono text-green-800">
            <div>Calibration scale calculated:</div>
            <div className="text-lg font-bold mt-1 text-green-950">
              {calibResult.scale_factor.toFixed(2)} px/mm
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
