import os
import re
import json
import base64
from io import BytesIO
from PIL import Image
from typing import List, Dict, Any, Optional

# Nominal dimensions in mm for standard packages
STANDARD_PACKAGES = [
    # Chip components (imperial)
    {"name": "0201", "type": "chip", "w": 0.6, "h": 0.3},
    {"name": "0402", "type": "chip", "w": 1.0, "h": 0.5},
    {"name": "0603", "type": "chip", "w": 1.6, "h": 0.8},
    {"name": "0805", "type": "chip", "w": 2.0, "h": 1.25},
    {"name": "1206", "type": "chip", "w": 3.2, "h": 1.6},
    {"name": "1210", "type": "chip", "w": 3.2, "h": 2.5},
    {"name": "2010", "type": "chip", "w": 5.0, "h": 2.5},
    {"name": "2512", "type": "chip", "w": 6.4, "h": 3.2},
    
    # Transistors
    {"name": "SOT-23", "type": "transistor", "w": 2.9, "h": 1.3},
    {"name": "SOT-223", "type": "transistor", "w": 6.5, "h": 3.5},
    {"name": "SOT-89", "type": "transistor", "w": 4.5, "h": 2.5},
    {"name": "DPAK", "type": "transistor", "w": 6.5, "h": 6.0},
    
    # Diodes
    {"name": "SOD-323", "type": "diode", "w": 1.7, "h": 1.25},
    {"name": "SOD-123", "type": "diode", "w": 2.7, "h": 1.6},
    {"name": "SMA", "type": "diode", "w": 4.3, "h": 2.6},
    {"name": "SMB", "type": "diode", "w": 4.6, "h": 3.6},
    {"name": "SMC", "type": "diode", "w": 7.0, "h": 6.0},
    
    # IC Packages (rough body dimensions)
    {"name": "SOIC-8", "type": "ic", "w": 4.9, "h": 3.9},
    {"name": "SOIC-14", "type": "ic", "w": 8.7, "h": 3.9},
    {"name": "SOIC-16", "type": "ic", "w": 9.9, "h": 3.9},
    {"name": "TSSOP-14", "type": "ic", "w": 5.0, "h": 4.4},
    {"name": "TSSOP-16", "type": "ic", "w": 5.0, "h": 4.4},
    {"name": "QFN-16", "type": "ic", "w": 3.0, "h": 3.0},
    {"name": "QFN-32", "type": "ic", "w": 5.0, "h": 5.0},
    {"name": "QFP-48", "type": "ic", "w": 7.0, "h": 7.0},
    {"name": "QFP-64", "type": "ic", "w": 10.0, "h": 10.0},
    {"name": "BGA", "type": "ic", "w": 12.0, "h": 12.0},
]

PREFIX_MAP = {
    "R": "resistor",
    "C": "capacitor",
    "L": "inductor",
    "U": "integrated_circuit",
    "Q": "transistor",
    "D": "diode",
    "LED": "led",
    "J": "connector",
    "CN": "connector",
    "Y": "crystal",
    "X": "crystal",
    "SW": "switch",
    "F": "fuse",
    "TP": "test_point",
    "FB": "ferrite_bead",
    "RN": "resistor_network",
    "T": "transformer"
}

def get_class_from_designator(designator: Optional[str], default_class: str) -> str:
    if not designator:
        return default_class
    # Match alphabetical prefix
    match = re.match(r"^([a-zA-Z]+)", designator)
    if match:
        prefix = match.group(1).upper()
        if prefix in PREFIX_MAP:
            return PREFIX_MAP[prefix]
        # Check sub-prefix (e.g. LED)
        for p in sorted(PREFIX_MAP.keys(), key=len, reverse=True):
            if prefix.startswith(p):
                return PREFIX_MAP[p]
    return default_class

def calculate_iou(boxA, boxB):
    xA = max(boxA["xmin"], boxB["xmin"])
    yA = max(boxA["ymin"], boxB["ymin"])
    xB = min(boxA["xmax"], boxB["xmax"])
    yB = min(boxA["ymax"], boxB["ymax"])
    
    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA["xmax"] - boxA["xmin"]) * (boxA["ymax"] - boxA["ymin"])
    boxBArea = (boxB["xmax"] - boxB["xmin"]) * (boxB["ymax"] - boxB["ymin"])
    
    unionArea = boxAArea + boxBArea - interArea
    if unionArea == 0:
        return 0.0
    return interArea / unionArea

def infer_package(measured_w: float, measured_h: float, component_class: str) -> Dict[str, Any]:
    best_match = None
    best_error = 999.0
    
    # Orientations: check both (w, h) and (h, w)
    for pkg in STANDARD_PACKAGES:
        # Compute dimensional error ratio
        # Option 1: w matching measured_w, h matching measured_h
        err_w1 = abs(measured_w - pkg["w"]) / pkg["w"]
        err_h1 = abs(measured_h - pkg["h"]) / pkg["h"]
        diff1 = max(err_w1, err_h1)
        
        # Option 2: w matching measured_h, h matching measured_w
        err_w2 = abs(measured_w - pkg["h"]) / pkg["h"]
        err_h2 = abs(measured_h - pkg["w"]) / pkg["w"]
        diff2 = max(err_w2, err_h2)
        
        match_err = min(diff1, diff2)
        if match_err < best_error:
            best_error = match_err
            best_match = pkg
            
    # Standard threshold: 20% tolerance
    if best_match and best_error < 0.20:
        return {
            "package": best_match["name"],
            "package_status": "resolved"
        }
    else:
        return {
            "package": f"{measured_w:.1f}x{measured_h:.1f}mm",
            "package_status": "unresolved"
        }

def get_tiles(img_w: int, img_h: int, rows: int = 3, cols: int = 3, overlap: float = 0.15) -> List[Dict[str, Any]]:
    # Calculate tile width and height
    # W = cols * w - (cols - 1) * w * overlap
    # w = W / (cols - (cols - 1) * overlap)
    tile_w = img_w / (cols - (cols - 1) * overlap) if cols > 1 else img_w
    tile_h = img_h / (rows - (rows - 1) * overlap) if rows > 1 else img_h
    
    step_x = tile_w * (1.0 - overlap) if cols > 1 else 0
    step_y = tile_h * (1.0 - overlap) if rows > 1 else 0
    
    tiles = []
    for r in range(rows):
        for c in range(cols):
            x_start = c * step_x
            y_start = r * step_y
            
            # Snap final tiles to edge to prevent off-by-one pixel gaps
            if c == cols - 1:
                x_start = img_w - tile_w
            if r == rows - 1:
                y_start = img_h - tile_h
                
            tiles.append({
                "row": r,
                "col": c,
                "x_start": max(0.0, x_start),
                "y_start": max(0.0, y_start),
                "w": tile_w,
                "h": tile_h
            })
    return tiles

async def analyze_tile(image_base64: str, api_provider: str) -> List[Dict[str, Any]]:
    # Checks environment variables for actual API calls
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    system_instruction = (
        "You are an expert electronics cost engineer. Inspect the provided PCB image tile and extract all visible components. "
        "Return a JSON array of objects. Do not write markdown text, just the raw JSON array. "
        "For each component, provide:\n"
        "- 'designator': Silkscreen designator (e.g. 'R12', 'C5', 'U1'). If not fully legible, return null.\n"
        "- 'class_guess': Inferred component class based on look (e.g. 'resistor', 'capacitor', 'diode', 'transistor', 'integrated_circuit') if designator is null.\n"
        "- 'bbox': Relative boundary coordinates [ymin, xmin, ymax, xmax] scaled 0 to 1000.\n"
        "- 'marking_text': Exact markings, logos, numbers on the component body. Return null if none or unreadable.\n"
        "- 'visual_notes': Details on colors, shapes, heights.\n"
        "- 'confidence': 'high', 'medium', or 'low'.\n"
        "Be extremely conservative: do not guess values for blank capacitors or resistors. Mark illegible fields as null."
    )

    if api_provider == "claude" and anthropic_key:
        try:
            import anthropic
            client = anthropic.Client(api_key=anthropic_key)
            # Invoke Claude 3.5 Sonnet
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_instruction,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": "Extract all components in this tile."
                            }
                        ]
                    }
                ]
            )
            # Parse response text (handle potential markdown blocks)
            text_resp = message.content[0].text
            cleaned = re.sub(r"^```json\s*", "", text_resp, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned.strip())
        except Exception as e:
            print(f"Claude API failed: {e}")
            raise e
            
    elif api_provider == "gemini" and gemini_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            # Invoke Gemini 2.5 Flash with schema output
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=base64.b64decode(image_base64),
                        mime_type='image/jpeg',
                    ),
                    "Extract components as JSON array matching instructions: " + system_instruction
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            text_resp = response.text
            return json.loads(text_resp.strip())
        except Exception as e:
            print(f"Gemini API failed: {e}")
            raise e
            
    # If no key, raise error to trigger mock detection
    raise ValueError("No API Key configured.")

def merge_detections(raw_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 1. Group by designator (for those that have designator)
    named_detections = {}
    anonymous_detections = []
    
    for det in raw_detections:
        des = det.get("designator")
        if des:
            # clean designator name
            des_clean = des.strip().upper()
            if des_clean not in named_detections:
                named_detections[des_clean] = []
            named_detections[des_clean].append(det)
        else:
            anonymous_detections.append(det)
            
    merged = []
    
    # 2. Merge named duplicates
    confidence_scores = {"high": 3, "medium": 2, "low": 1}
    for des, group in named_detections.items():
        # Pick best: highest confidence, then largest bbox area
        def get_sort_key(d):
            score = confidence_scores.get(d["confidence"].lower(), 1)
            bbox = d["bbox"]
            area = (bbox["xmax"] - bbox["xmin"]) * (bbox["ymax"] - bbox["ymin"])
            return (score, area)
            
        group.sort(key=get_sort_key, reverse=True)
        best = group[0]
        
        # Override class deterministically
        best["component_class"] = get_class_from_designator(des, best.get("component_class", "resistor"))
        merged.append(best)
        
    # 3. Merge anonymous detections using IoU deduplication (greedy Non-Maximum Suppression)
    # Sort anonymous by bbox area descending
    def get_area(d):
        bbox = d["bbox"]
        return (bbox["xmax"] - bbox["xmin"]) * (bbox["ymax"] - bbox["ymin"])
        
    anonymous_detections.sort(key=get_area, reverse=True)
    
    kept_anonymous = []
    for det in anonymous_detections:
        # Check IoU overlap against already kept detections (both named and anonymous)
        overlap = False
        for kept in merged + kept_anonymous:
            iou = calculate_iou(det["bbox"], kept["bbox"])
            if iou > 0.5:
                overlap = True
                # Merge marking text if the duplicate has better marking
                if not kept.get("marking_text") and det.get("marking_text"):
                    kept["marking_text"] = det["marking_text"]
                break
        if not overlap:
            # Deterministically clean anonymous guess
            det["component_class"] = get_class_from_designator(None, det.get("class_guess", "resistor"))
            kept_anonymous.append(det)
            
    merged.extend(kept_anonymous)
    return merged

# HIGH QUALITY MOCK DETECTOR FOR TESTING
def generate_mock_detections(filename: str, img_w: int, img_h: int) -> List[Dict[str, Any]]:
    # Create realistic detections for RPi boards or generic board
    is_rpi = "raspberry" in filename.lower() or "pi" in filename.lower() or "dsc" in filename.lower()
    
    detections = []
    
    if is_rpi:
        # CPU
        detections.append({
            "designator": "U1",
            "component_class": "integrated_circuit",
            "bbox": {"xmin": int(img_w * 0.42), "ymin": int(img_h * 0.38), "xmax": int(img_w * 0.58), "ymax": int(img_h * 0.62)},
            "marking_text": "BCM2837RIFBG",
            "visual_notes": "Large black square package with Broadcom logo",
            "confidence": "high"
        })
        # RAM
        detections.append({
            "designator": "U2",
            "component_class": "integrated_circuit",
            "bbox": {"xmin": int(img_w * 0.62), "ymin": int(img_h * 0.40), "xmax": int(img_w * 0.74), "ymax": int(img_h * 0.58)},
            "marking_text": "ELPIDA B8132B4",
            "visual_notes": "Rectangular black IC, Elpida RAM chip",
            "confidence": "high"
        })
        # USB/LAN Controller
        detections.append({
            "designator": "U3",
            "component_class": "integrated_circuit",
            "bbox": {"xmin": int(img_w * 0.78), "ymin": int(img_h * 0.20), "xmax": int(img_w * 0.86), "ymax": int(img_h * 0.34)},
            "marking_text": "LAN9514-JZX",
            "visual_notes": "Small QFN-like integrated circuit",
            "confidence": "medium"
        })
        # Power Management PMIC
        detections.append({
            "designator": "U4",
            "component_class": "integrated_circuit",
            "bbox": {"xmin": int(img_w * 0.20), "ymin": int(img_h * 0.70), "xmax": int(img_w * 0.28), "ymax": int(img_h * 0.82)},
            "marking_text": "PAM2306",
            "visual_notes": "Power converter IC near microUSB input",
            "confidence": "high"
        })
        # Crystal
        detections.append({
            "designator": "Y1",
            "component_class": "crystal",
            "bbox": {"xmin": int(img_w * 0.35), "ymin": int(img_h * 0.30), "xmax": int(img_w * 0.39), "ymax": int(img_h * 0.36)},
            "marking_text": "19.2 MHz",
            "visual_notes": "Metallic oval crystal package",
            "confidence": "high"
        })
        # USB Port
        detections.append({
            "designator": "J1",
            "component_class": "connector",
            "bbox": {"xmin": int(img_w * 0.84), "ymin": int(img_h * 0.65), "xmax": int(img_w * 0.98), "ymax": int(img_h * 0.90)},
            "marking_text": "USB-A",
            "visual_notes": "Double stacked metal USB type A port",
            "confidence": "high"
        })
        # HDMI Port
        detections.append({
            "designator": "J2",
            "component_class": "connector",
            "bbox": {"xmin": int(img_w * 0.40), "ymin": int(img_h * 0.02), "xmax": int(img_w * 0.55), "ymax": int(img_h * 0.12)},
            "marking_text": "HDMI",
            "visual_notes": "Metal shielded HDMI female port",
            "confidence": "high"
        })
        
        # Add various passives (resistors/capacitors)
        passives = [
            ("C1", "capacitor", 0.32, 0.45, 12, 8, None, "Brown chip cap"),
            ("C2", "capacitor", 0.34, 0.46, 12, 8, None, "Brown chip cap"),
            ("C3", "capacitor", 0.45, 0.33, 16, 12, None, "Large brown capacitor"),
            ("C4", "capacitor", 0.48, 0.33, 16, 12, None, "Large brown capacitor"),
            ("C5", "capacitor", 0.61, 0.38, 12, 8, None, "Decoupling capacitor"),
            ("C6", "capacitor", 0.22, 0.75, 16, 12, None, "Tantalum yellow capacitor"),
            ("R1", "resistor", 0.43, 0.35, 12, 8, "103", "Black chip resistor"),
            ("R2", "resistor", 0.44, 0.35, 12, 8, "472", "Black chip resistor"),
            ("R3", "resistor", 0.59, 0.42, 10, 5, None, "Small unmarked chip resistor"),
            ("R4", "resistor", 0.60, 0.42, 10, 5, None, "Small unmarked chip resistor"),
            ("R5", "resistor", 0.77, 0.25, 12, 8, "100", "Series termination resistor"),
            ("D1", "diode", 0.15, 0.85, 20, 15, "SS14", "Black Schottky diode"),
            ("L1", "inductor", 0.25, 0.65, 30, 30, "4R7", "Shielded power inductor"),
            ("Q1", "transistor", 0.30, 0.78, 25, 15, "W2F", "SOT-23 transistor"),
        ]
        
        for name, comp_class, rx, ry, w_val, h_val, marking, note in passives:
            # Map center ratios back to dimensions
            cx, cy = int(img_w * rx), int(img_h * ry)
            detections.append({
                "designator": name,
                "component_class": comp_class,
                "bbox": {"xmin": cx - w_val, "ymin": cy - h_val, "xmax": cx + w_val, "ymax": cy + h_val},
                "marking_text": marking,
                "visual_notes": note,
                "confidence": "high" if marking else "medium"
            })
            
        # Add 5 anonymous detections to test review workflows
        for i in range(5):
            cx, cy = int(img_w * (0.15 + i * 0.12)), int(img_h * (0.15 + i * 0.08))
            detections.append({
                "designator": None,
                "component_class": "capacitor" if i % 2 == 0 else "resistor",
                "bbox": {"xmin": cx - 8, "ymin": cy - 6, "xmax": cx + 8, "ymax": cy + 6},
                "marking_text": None,
                "visual_notes": "Small passive component without silkscreen text",
                "confidence": "low"
            })
            
    else:
        # Default mock output for custom board
        # 1 IC, 1 connector, 6 passives
        detections.append({
            "designator": "U1",
            "component_class": "integrated_circuit",
            "bbox": {"xmin": int(img_w * 0.35), "ymin": int(img_h * 0.35), "xmax": int(img_w * 0.65), "ymax": int(img_h * 0.65)},
            "marking_text": "STM32F103C8T6",
            "visual_notes": "LQFP-48 chip package",
            "confidence": "high"
        })
        
        detections.append({
            "designator": "J1",
            "component_class": "connector",
            "bbox": {"xmin": int(img_w * 0.02), "ymin": int(img_h * 0.40), "xmax": int(img_w * 0.15), "ymax": int(img_h * 0.60)},
            "marking_text": "USB-MINI",
            "visual_notes": "Mini USB port connector",
            "confidence": "high"
        })
        
        for i in range(1, 5):
            cx = int(img_w * (0.25 + i * 0.10))
            cy = int(img_h * 0.25)
            detections.append({
                "designator": f"R{i}",
                "component_class": "resistor",
                "bbox": {"xmin": cx - 12, "ymin": cy - 8, "xmax": cx + 12, "ymax": cy + 8},
                "marking_text": "1002" if i % 2 == 0 else None,
                "visual_notes": "Unmarked or 10k chip resistor",
                "confidence": "high" if i % 2 == 0 else "medium"
            })
            
        for i in range(1, 5):
            cx = int(img_w * (0.25 + i * 0.10))
            cy = int(img_h * 0.75)
            detections.append({
                "designator": f"C{i}",
                "component_class": "capacitor",
                "bbox": {"xmin": cx - 12, "ymin": cy - 8, "xmax": cx + 12, "ymax": cy + 8},
                "marking_text": None,
                "visual_notes": "Brown ceramic capacitor",
                "confidence": "medium"
            })
            
    return detections
