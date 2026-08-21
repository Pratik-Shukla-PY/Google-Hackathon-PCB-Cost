# PCB Cost BOM Generator

A specialized web application for hardware cost engineers and competitor teardown analysis. It accepts a high-resolution photograph of a populated printed circuit board, calibrates physical scale, detects component packages, groups BOM line items, and exports a costed Bill of Materials (BOM) in Excel with live volume-based pricing breaks.

---

## Key Features

1. **High-Resolution Upload Validation**: Validates that board photos have at least 2000px on the long edge to ensure component markings are legible.
2. **Scale Calibration & Skew Detection**: Interactive canvas allowing users to draw a reference box of known physical dimensions (mm). Automatically flags and warns if perspective distortion/skew exceeds 5%.
3. **Smart Package Inference**: Snaps measured physical dimensions to standard footprints (0201, 0402, 0603, 0805, 1206, SOT-23, SOIC-8, etc.) using a 20% tolerance band.
4. **Interactive Review Workspace**: Split-view UI with bidirectional hover highlighting between board bounding boxes and the component table. Supports manual component drawing, deletion, inline field editing, and confidence filtering.
5. **Costing & Sourcing Engine**: Groups detections into line items, matches identified silicon or generic passives, applies tiered quantity pricing breaks based on annual build volume, and flags generic assumptions.
6. **Multi-Sheet Excel Export**: Generates styled `.xlsx` workbooks with:
   - **Cost BOM**: Styled headers, conditional cell shading for generic parts, live datasheet hyperlinks, and total formulas.
   - **Detections**: Audit trail showing pixel coordinates and measured dimensions.
   - **Run Summary**: Metadata and standard teardown exclusions disclaimer.

---

## Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide Icons, React Router DOM.
- **Backend**: Python 3.11, FastAPI, Uvicorn, Pillow (Image Processing), openpyxl (Excel Export), SQLite.
- **Vision Integration**: Claude 3.5 Sonnet / Gemini 2.5 Flash (with high-fidelity offline mock fallback).

---

## Local Development Setup

### 1. Backend Setup

```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Start the FastAPI server on port 8000
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Deploying to GitHub and Vercel

### Step 1: Push to GitHub

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: PCB Cost BOM Generator"

# Link to your GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Backend (e.g. Render / Railway / Google Cloud Run)

Deploy the `backend` folder as a Python web service:
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables (Optional)**:
  - `ANTHROPIC_API_KEY`: Your Claude API key for live vision model extraction.
  - `GEMINI_API_KEY`: Your Gemini API key.

### Step 3: Deploy Frontend to Vercel

1. Go to [Vercel](https://vercel.com) and click **Add New Project**.
2. Import your GitHub repository.
3. In **Project Settings**:
   - **Root Directory**: Set to `frontend`
   - **Framework Preset**: `Vite`
   - **Environment Variables**:
     - `VITE_API_BASE_URL`: Set to your deployed backend URL (e.g., `https://your-backend-api.onrender.com`).
4. Click **Deploy**.
