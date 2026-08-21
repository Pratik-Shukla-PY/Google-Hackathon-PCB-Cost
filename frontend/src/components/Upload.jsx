import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Upload as UploadIcon, AlertCircle, Camera, CheckCircle2 } from "lucide-react"
import { API_BASE_URL } from "../config"

export default function Upload() {
  const navigate = useNavigate()
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [error, setError] = useState("")
  const [uploading, setUploading] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const validateAndSetFile = (selectedFile) => {
    setError("")
    if (!selectedFile) return

    // Limit to 20MB
    if (selectedFile.size > 20 * 1024 * 1024) {
      setError("File size exceeds the 20 MB limit. Please upload a smaller image.")
      return
    }

    if (!selectedFile.type.startsWith("image/jpeg") && !selectedFile.type.startsWith("image/png")) {
      setError("Unsupported file format. Please upload a JPEG or PNG image.")
      return
    }

    // Client-side image dimensions validation
    const img = new Image()
    img.src = URL.createObjectURL(selectedFile)
    img.onload = () => {
      const longEdge = Math.max(img.width, img.height)
      if (longEdge < 2000) {
        setError(`Image resolution is too low (${img.width}x${img.height}px). The long edge must be at least 2000 pixels to ensure component markings are legible.`)
      } else {
        setFile(selectedFile)
        setPreviewUrl(URL.createObjectURL(selectedFile))
      }
    }
    img.onerror = () => {
      setError("Invalid image file. Could not read image properties.")
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const handleUploadSubmit = async () => {
    if (!file) return
    setUploading(true)
    setError("")

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/projects`, {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed")
      }

      navigate(`/calibrate/${data.id}`)
    } catch (err) {
      console.error(err)
      setError(err.message || "Failed to upload image. Please ensure the backend is running.")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-8 flex flex-col md:grid md:grid-cols-5 gap-8">
      {/* Upload Zone & Preview: 3 cols */}
      <div className="md:col-span-3 flex flex-col gap-6">
        <div className="bg-white border border-slate-200 rounded p-6 shadow-sm flex-1 flex flex-col">
          <h2 className="text-lg font-bold font-mono text-slate-800 mb-4">Board Photograph Upload</h2>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded p-3 flex gap-3 text-red-700 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <div>{error}</div>
            </div>
          )}

          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`flex-1 min-h-[300px] border-2 border-dashed rounded flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-colors relative ${
              dragActive ? "border-blue-500 bg-blue-50/20" : "border-slate-300 hover:border-slate-400 bg-slate-50/30"
            }`}
          >
            <input
              type="file"
              id="file-upload-input"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleChange}
              accept=".jpg,.jpeg,.png"
            />
            {previewUrl ? (
              <div className="w-full h-full flex flex-col items-center justify-center gap-4">
                <img
                  src={previewUrl}
                  alt="Board preview"
                  className="max-h-[280px] max-w-full object-contain rounded border border-slate-200 shadow-sm"
                />
                <span className="text-xs text-slate-500 font-mono">
                  {file.name} ({Math.round(file.size / 1024 / 1024 * 100) / 100} MB)
                </span>
                <span className="text-xs text-blue-600 underline">Choose a different file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-full shadow-sm">
                  <UploadIcon className="w-6 h-6 text-slate-500" />
                </div>
                <div className="text-sm font-medium text-slate-700">
                  Drag and drop your board image here
                </div>
                <div className="text-xs text-slate-400">
                  JPEG or PNG up to 20 MB (min. 2000px on long edge)
                </div>
                <button className="mt-2 px-3 py-1.5 bg-white border border-slate-300 rounded shadow-sm text-xs font-medium text-slate-700 hover:bg-slate-50">
                  Select File
                </button>
              </div>
            )}
          </div>

          {/* Action Button */}
          {file && (
            <button
              onClick={handleUploadSubmit}
              disabled={uploading}
              className="w-full mt-6 bg-slate-800 text-white py-3 rounded text-sm font-medium hover:bg-slate-700 active:bg-slate-900 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {uploading ? "Uploading & Initializing..." : "Proceed to Scale Calibration"}
            </button>
          )}
        </div>
      </div>

      {/* Guidelines: 2 cols */}
      <div className="md:col-span-2 flex flex-col gap-6">
        <div className="bg-white border border-slate-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Camera className="w-5 h-5 text-slate-700" />
            <h3 className="font-mono font-bold text-slate-800">Capture Guidance</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4 leading-relaxed">
            Teardown costing accuracy depends entirely on image quality. Poor photographs lead to failed detection and incorrect part numbers.
          </p>

          <ul className="space-y-4">
            <li className="flex gap-3">
              <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-700 font-mono">Shoot Straight Down</h4>
                <p className="text-xs text-slate-400 mt-1 leading-normal">
                  Align camera perpendicular to board. Perspective distortion and tilt skew physical scaling.
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-700 font-mono">Use Diffuse, Even Light</h4>
                <p className="text-xs text-slate-400 mt-1 leading-normal">
                  Avoid direct flash or point lights. Glare on packages hides silicon part numbers and marking text.
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-700 font-mono">Fill the Frame</h4>
                <p className="text-xs text-slate-400 mt-1 leading-normal">
                  Get close to maximize resolution per passive component. Target high density over background whitespace.
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-700 font-mono">One Side Per Upload</h4>
                <p className="text-xs text-slate-400 mt-1 leading-normal">
                  Double-sided merges are out of scope. Process each face as a separate teardown run.
                </p>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
