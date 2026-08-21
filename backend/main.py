import os
import uuid
import datetime
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from vision import get_tiles, analyze_tile, merge_detections, infer_package, generate_mock_detections

from database import (
    init_db,
    insert_project,
    get_project,
    get_all_projects,
    update_project_calibration,
    update_project_volume,
    insert_detections,
    get_project_detections,
    update_detection,
    delete_detection,
    add_manual_detection
)
from models import Project, DetectionBase, CalibrationRequest

app = FastAPI(title="PCB Cost BOM Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount uploads static directory so images can be served to the frontend
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Initialize database immediately to ensure tables are always created
init_db()

@app.on_event("startup")
def startup_event():
    pass

# AUTHENTICATION ROUTE (STUB)
@app.post("/api/auth/login")
def login():
    # Set a dummy cookie/token for session verification
    return {
        "status": "success",
        "user": {
            "email": "cost_engineer@example.com",
            "name": "Teardown Specialist",
            "role": "Cost Engineer"
        }
    }

@app.get("/api/auth/session")
def session():
    return {
        "authenticated": True,
        "user": {
            "email": "cost_engineer@example.com",
            "name": "Teardown Specialist",
            "role": "Cost Engineer"
        }
    }

# UPLOAD ROUTE
@app.post("/api/projects")
async def upload_board_image(file: UploadFile = File(...)):
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported.")
    
    # Save the file temporarily to inspect dimensions
    project_id = str(uuid.uuid4())
    temp_filename = f"{project_id}{ext}"
    temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)
    
    try:
        with open(temp_filepath, "wb") as buffer:
            content = await file.read()
            # Max file size limit: 20MB
            if len(content) > 20 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds the 20 MB limit.")
            buffer.write(content)
        
        # Verify image dimensions using PIL
        with Image.open(temp_filepath) as img:
            width, height = img.size
            long_edge = max(width, height)
            
            if long_edge < 2000:
                os.remove(temp_filepath)
                raise HTTPException(
                    status_code=400,
                    detail=f"Image resolution is too low ({width}x{height}). The long edge must be at least 2000 pixels to ensure component markings are legible."
                )
        
        # Save project in database
        created_at = datetime.datetime.utcnow().isoformat()
        insert_project(project_id, file.filename, temp_filename, width, height, created_at)
        
        return {
            "id": project_id,
            "filename": file.filename,
            "imageUrl": f"http://localhost:8000/uploads/{temp_filename}",
            "width": width,
            "height": height,
            "created_at": created_at
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

# GET ALL PROJECTS
@app.get("/api/projects")
def list_projects():
    projects = get_all_projects()
    # Map database records to have full image URLs
    for p in projects:
        p["imageUrl"] = f"http://localhost:8000/uploads/{p['filepath']}"
    return projects

# GET SINGLE PROJECT
@app.get("/api/projects/{project_id}")
def get_single_project(project_id: str):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    project["imageUrl"] = f"http://localhost:8000/uploads/{project['filepath']}"
    return project

# CALIBRATE PROJECT
@app.post("/api/projects/{project_id}/calibrate")
def calibrate_project(project_id: str, req: CalibrationRequest):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    if req.real_w <= 0 or req.real_h <= 0 or req.box_w <= 0 or req.box_h <= 0:
        raise HTTPException(status_code=400, detail="Dimensions must be positive values.")
        
    scale_x = req.box_w / req.real_w
    scale_y = req.box_h / req.real_h
    scale_avg = (scale_x + scale_y) / 2.0
    
    # Calculate skew
    min_scale = min(scale_x, scale_y)
    difference = abs(scale_x - scale_y) / min_scale if min_scale > 0 else 0
    is_skewed = difference > 0.05
    
    reference_box = {
        "box_x": req.box_x,
        "box_y": req.box_y,
        "box_w": req.box_w,
        "box_h": req.box_h,
        "real_w": req.real_w,
        "real_h": req.real_h,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "difference": difference,
        "is_skewed": is_skewed
    }
    
    update_project_calibration(project_id, scale_avg, reference_box)
    
    # Recalculate existing detections package sizes based on new scale factor
    existing_dets = get_project_detections(project_id, include_deleted=True)
    if existing_dets:
        for det in existing_dets:
            bbox = det["bbox"]
            px_w = bbox["xmax"] - bbox["xmin"]
            px_h = bbox["ymax"] - bbox["ymin"]
            measured_w = px_w / scale_avg
            measured_h = px_h / scale_avg
            
            pkg_info = infer_package(measured_w, measured_h, det["component_class"])
            
            update_detection(det["id"], {
                "measured_width": measured_w,
                "measured_height": measured_h,
                "package": pkg_info["package"],
                "package_status": pkg_info["package_status"]
            })
            
    return {
        "id": project_id,
        "scale_factor": scale_avg,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "difference": difference,
        "is_skewed": is_skewed,
        "reference_box": reference_box
    }

# RUN DETECTION PIPELINE
@app.post("/api/projects/{project_id}/detect")
async def run_detection(
    project_id: str, 
    rows: int = 3, 
    cols: int = 3, 
    overlap: float = 0.15, 
    provider: str = "claude"
):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    image_path = os.path.join(UPLOAD_DIR, project["filepath"])
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found.")
        
    # Check if there are already detections. If so, return them to avoid double-processing
    existing = get_project_detections(project_id, include_deleted=True)
    if existing:
        # Filter deleted for default return
        return [e for e in existing if not e["is_deleted"]]
        
    # Determine API availability
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    use_mock = not (anthropic_key or gemini_key)
    
    raw_detections = []
    
    if use_mock:
        # Offline/mock generation
        raw_detections = generate_mock_detections(project["filename"], project["width"], project["height"])
    else:
        try:
            img = Image.open(image_path)
            tiles = get_tiles(project["width"], project["height"], rows, cols, overlap)
            
            for tile in tiles:
                # Crop tile
                crop_box = (
                    int(tile["x_start"]),
                    int(tile["y_start"]),
                    int(tile["x_start"] + tile["w"]),
                    int(tile["y_start"] + tile["h"])
                )
                tile_img = img.crop(crop_box)
                
                # Base64 encode
                buffered = BytesIO()
                tile_img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Call LLM
                try:
                    # Select provider
                    selected_provider = "gemini" if (gemini_key and provider == "gemini") else "claude"
                    tile_dets = await analyze_tile(img_str, selected_provider)
                    
                    for det in tile_dets:
                        # bbox format: [ymin, xmin, ymax, xmax] relative 0-1000
                        ymin, xmin, ymax, xmax = det["bbox"]
                        
                        global_bbox = {
                            "xmin": tile["x_start"] + (xmin / 1000.0) * tile["w"],
                            "ymin": tile["y_start"] + (ymin / 1000.0) * tile["h"],
                            "xmax": tile["x_start"] + (xmax / 1000.0) * tile["w"],
                            "ymax": tile["y_start"] + (ymax / 1000.0) * tile["h"]
                        }
                        
                        raw_detections.append({
                            "designator": det.get("designator"),
                            "component_class": det.get("class_guess", "resistor"),
                            "bbox": global_bbox,
                            "marking_text": det.get("marking_text"),
                            "visual_notes": det.get("visual_notes"),
                            "confidence": det.get("confidence", "medium")
                        })
                except Exception as tile_err:
                    print(f"Error in tile row {tile['row']}, col {tile['col']}: {tile_err}")
            
            # Merge and deduplicate
            raw_detections = merge_detections(raw_detections)
            
        except Exception as e:
            print(f"Vision pipeline error: {e}. Falling back to mock data.")
            raw_detections = generate_mock_detections(project["filename"], project["width"], project["height"])
            
    # Resolve packages using calibration scale factor if available
    scale_factor = project["scale_factor"]
    for det in raw_detections:
        bbox = det["bbox"]
        px_w = bbox["xmax"] - bbox["xmin"]
        px_h = bbox["ymax"] - bbox["ymin"]
        
        if scale_factor:
            measured_w = px_w / scale_factor
            measured_h = px_h / scale_factor
            det["measured_width"] = measured_w
            det["measured_height"] = measured_h
            
            pkg_info = infer_package(measured_w, measured_h, det["component_class"])
            det["package"] = pkg_info["package"]
            det["package_status"] = pkg_info["package_status"]
        else:
            det["measured_width"] = None
            det["measured_height"] = None
            det["package"] = "Uncalibrated"
            det["package_status"] = "unresolved"
            
        det["manually_added"] = 0
        det["is_deleted"] = 0
        
    insert_detections(project_id, raw_detections)
    return get_project_detections(project_id)

# CRUD COMPONENT ROUTE: LIST COMPONENTS
@app.get("/api/projects/{project_id}/components")
def list_components(project_id: str):
    return get_project_detections(project_id)

# CRUD COMPONENT ROUTE: ADD COMPONENT
@app.post("/api/projects/{project_id}/components")
def add_component(project_id: str, det: DetectionBase):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    det_dict = det.dict()
    
    # If project scale factor exists, compute physical size and check package
    scale_factor = project["scale_factor"]
    px_w = det_dict["bbox"]["xmax"] - det_dict["bbox"]["xmin"]
    px_h = det_dict["bbox"]["ymax"] - det_dict["bbox"]["ymin"]
    
    if scale_factor:
        measured_w = px_w / scale_factor
        measured_h = px_h / scale_factor
        det_dict["measured_width"] = measured_w
        det_dict["measured_height"] = measured_h
        
        pkg_info = infer_package(measured_w, measured_h, det_dict["component_class"])
        # If user manually provided a package in the request, keep it. Otherwise resolve it.
        if not det_dict.get("package"):
            det_dict["package"] = pkg_info["package"]
            det_dict["package_status"] = pkg_info["package_status"]
    else:
        det_dict["measured_width"] = None
        det_dict["measured_height"] = None
        if not det_dict.get("package"):
            det_dict["package"] = "Uncalibrated"
            det_dict["package_status"] = "unresolved"
            
    last_id = add_manual_detection(project_id, det_dict)
    
    # Return full object
    return {
        "id": last_id,
        "project_id": project_id,
        **det_dict
    }

# CRUD COMPONENT ROUTE: UPDATE COMPONENT
@app.put("/api/projects/{project_id}/components/{detection_id}")
def update_project_component(project_id: str, detection_id: int, updates: Dict[str, Any]):
    # Prevent SQL injection/column issues by filtering update fields
    allowed_fields = [
        "designator", "component_class", "marking_text", "visual_notes", 
        "confidence", "package", "measured_width", "measured_height", 
        "package_status", "is_deleted", "bbox"
    ]
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    update_detection(detection_id, filtered_updates)
    return {"status": "success", "id": detection_id}

# CRUD COMPONENT ROUTE: DELETE COMPONENT
@app.delete("/api/projects/{project_id}/components/{detection_id}")
def delete_project_component(project_id: str, detection_id: int):
    delete_detection(detection_id)
    return {"status": "success", "id": detection_id}

# UPDATE PROJECT VOLUME
@app.post("/api/projects/{project_id}/volume")
def update_volume(project_id: str, volume: int):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    update_project_volume(project_id, volume)
    return {"status": "success", "build_volume": volume}

# GET COST BOM
@app.get("/api/projects/{project_id}/cost")
def get_project_cost_bom(project_id: str):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    detections = get_project_detections(project_id)
    if not detections:
        return {
            "summary": {
                "total_line_items": 0,
                "total_components": 0,
                "board_cost": 0.0,
                "generic_costed_count": 0
            },
            "rows": []
        }
        
    # Group detections: (class, package, marking_text)
    groups = {}
    for det in detections:
        if det["is_deleted"]:
            continue
        key = (
            det["component_class"],
            det.get("package") or "",
            det.get("marking_text") or ""
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(det)
        
    bom_rows = []
    line_number = 1
    
    total_components = 0
    generic_costed_count = 0
    board_cost = 0.0
    
    from sourcing import perform_sourcing_lookup
    
    for key, group in groups.items():
        comp_class, package, marking_text = key
        qty = len(group)
        total_components += qty
        
        # Designators list
        designators_list = sorted([d["designator"] for d in group if d.get("designator")])
        designators_str = ", ".join(designators_list) if designators_list else "Anon"
        
        # Average measured sizes
        lengths = [d["measured_width"] for d in group if d.get("measured_width") is not None]
        widths = [d["measured_height"] for d in group if d.get("measured_height") is not None]
        
        avg_len = sum(lengths) / len(lengths) if lengths else None
        avg_wid = sum(widths) / len(widths) if widths else None
        
        # Package resolution status
        pkg_statuses = [d["package_status"] for d in group]
        status = "resolved" if "resolved" in pkg_statuses else "unresolved"
        
        # Confidence resolution (lowest confidence determines the group confidence)
        conf_scores = {"low": 1, "medium": 2, "high": 3}
        lowest_conf = "high"
        min_score = 4
        for d in group:
            score = conf_scores.get(d["confidence"].lower(), 2)
            if score < min_score:
                min_score = score
                lowest_conf = d["confidence"]
                
        # Call sourcing matching
        sourcing = perform_sourcing_lookup(
            comp_class,
            package if package else None,
            marking_text if marking_text else None,
            project["build_volume"],
            qty
        )
        
        is_generic = sourcing["match_basis"].lower() == "generic"
        if is_generic:
            generic_costed_count += 1
            
        unit_price = sourcing["unit_price"]
        extended_cost = unit_price * qty
        board_cost += extended_cost
        
        has_marking = bool(marking_text)
        
        bom_row = {
            "line_number": line_number,
            "component_class": comp_class,
            "designators": designators_str,
            "quantity": qty,
            "marking_text": marking_text if marking_text else None,
            "package": package if package else "Unknown",
            "measured_length": avg_len,
            "measured_width": avg_wid,
            "package_resolution_status": status,
            
            # Sourcing
            "manufacturer": sourcing["manufacturer"],
            "part_number": sourcing["part_number"],
            "description": sourcing["description"],
            "distributor": sourcing["distributor"],
            "distributor_part_number": sourcing["distributor_part_number"],
            "datasheet_url": sourcing["datasheet_url"],
            "product_page_url": sourcing["product_page_url"],
            "match_basis": sourcing["match_basis"],
            
            # Pricing
            "unit_price": unit_price,
            "currency": "USD",
            "price_break_qty": sourcing["price_break_qty"],
            "moq": sourcing["moq"],
            "stock_status": sourcing["stock_status"],
            "extended_cost": extended_cost,
            "price_date": sourcing["price_date"],
            
            # Provenance
            "confidence": lowest_conf,
            "manufacturer_read": has_marking,
            "part_number_read": has_marking,
            "price_read": not is_generic,
            "note": sourcing.get("note") or (f"Assumed generic standard {package} {comp_class}." if is_generic else None)
        }
        
        bom_rows.append(bom_row)
        line_number += 1
        
    return {
        "summary": {
            "total_line_items": len(bom_rows),
            "total_components": total_components,
            "board_cost": board_cost,
            "generic_costed_count": generic_costed_count
        },
        "rows": bom_rows
    }

# EXCEL EXPORT ROUTE
@app.get("/api/projects/{project_id}/export")
def export_project_bom(project_id: str):
    from fastapi.responses import FileResponse
    
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    bom_data = get_project_cost_bom(project_id)
    detections = get_project_detections(project_id)
    
    base_name = os.path.splitext(project["filename"])[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"{base_name}_BOM_{timestamp}.xlsx"
    excel_filepath = os.path.join(UPLOAD_DIR, excel_filename)
    
    from excel import generate_bom_excel
    generate_bom_excel(project, bom_data["rows"], detections, excel_filepath)
    
    return FileResponse(
        path=excel_filepath,
        filename=excel_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
