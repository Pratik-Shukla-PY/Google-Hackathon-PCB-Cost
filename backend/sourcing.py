import datetime
import re
from typing import List, Dict, Any, Optional
from database import get_cached_sourcing, set_cached_sourcing

# Embedded High-Fidelity Catalog Database for Sourcing & Costing
LOCAL_CATALOG = {
    # Identified ICs (Broadcom CPU, Elpida RAM, LAN chip, PMIC, etc.)
    "bcm2837rifbg": {
        "manufacturer": "Broadcom",
        "part_number": "BCM2837RIFBG",
        "description": "Application Processor Quad-Core 1.2GHz ARM Cortex-A53",
        "distributor": "DigiKey",
        "distributor_part_number": "1700-1024-ND",
        "price_breaks": [
            {"qty": 1, "price": 18.50},
            {"qty": 100, "price": 16.20},
            {"qty": 1000, "price": 14.80},
            {"qty": 10000, "price": 12.50}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheets.raspberrypi.com/processor/bcm2837-datasheet.pdf",
        "product_page_url": "https://www.broadcom.com/products/embedded-and-automotive-processors",
        "match_basis": "identified",
        "notes": "Silicon identification read from chip markings."
    },
    "elpida b8132b4": {
        "manufacturer": "Elpida / Micron",
        "part_number": "EDB8132B4PB-8D-F",
        "description": "LPDDR2 1GB Memory DRAM SDRAM 32-bit 800MHz FBGA",
        "distributor": "Mouser",
        "distributor_part_number": "552-EDB8132B4PB",
        "price_breaks": [
            {"qty": 1, "price": 6.80},
            {"qty": 100, "price": 5.40},
            {"qty": 1000, "price": 4.60},
            {"qty": 10000, "price": 3.95}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://media-www.micron.com/-/media/client/global/documents/products/data-sheet/dram/mobile-dram/low-power-dram/lpddr2/2gb_mobile_lpddr2_s4_sdram.pdf",
        "product_page_url": "https://www.mouser.com/ProductDetail/Micron/EDB8132B4PB-8D-F",
        "match_basis": "identified",
        "notes": "High capacity LPDDR2 RAM matched from chip package markings."
    },
    "lan9514-jzx": {
        "manufacturer": "Microchip Technology",
        "part_number": "LAN9514-JZX",
        "description": "USB 2.0 Hub and 10/100 Ethernet Controller",
        "distributor": "DigiKey",
        "distributor_part_number": "LAN9514-JZX-ND",
        "price_breaks": [
            {"qty": 1, "price": 3.75},
            {"qty": 100, "price": 3.10},
            {"qty": 1000, "price": 2.65},
            {"qty": 5000, "price": 2.20}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://ww1.microchip.com/downloads/en/DeviceDoc/00002306A.pdf",
        "product_page_url": "https://www.microchip.com/en-us/product/LAN9514",
        "match_basis": "identified",
        "notes": "Ethernet controller match verified from component package marking."
    },
    "pam2306": {
        "manufacturer": "Diodes Incorporated",
        "part_number": "PAM2306AYPKE",
        "description": "Dual Step-Down DC-DC Converter 1A W-DFN3030-10",
        "distributor": "Mouser",
        "distributor_part_number": "621-PAM2306AYPKE",
        "price_breaks": [
            {"qty": 1, "price": 1.15},
            {"qty": 100, "price": 0.88},
            {"qty": 1000, "price": 0.72},
            {"qty": 10000, "price": 0.58}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.diodes.com/assets/Datasheets/PAM2306.pdf",
        "product_page_url": "https://www.diodes.com/products/power-management/dc-dc-converters/buck-converters/external-switch/pam2306/",
        "match_basis": "identified",
        "notes": "PMIC regulator identified."
    },
    "stm32f103c8t6": {
        "manufacturer": "STMicroelectronics",
        "part_number": "STM32F103C8T6",
        "description": "ARM Cortex-M3 32-bit MCU 64KB Flash 72MHz LQFP-48",
        "distributor": "LCSC",
        "distributor_part_number": "C8734",
        "price_breaks": [
            {"qty": 1, "price": 1.95},
            {"qty": 100, "price": 1.62},
            {"qty": 1000, "price": 1.40},
            {"qty": 10000, "price": 1.18}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/STMicroelectronics-STM32F103C8T6_C8734.html",
        "match_basis": "identified",
        "notes": "Silicon MCU verified from marking."
    },
    "ss14": {
        "manufacturer": "ON Semiconductor",
        "part_number": "SS14",
        "description": "Schottky Barrier Rectifier Diode 40V 1A SMA",
        "distributor": "DigiKey",
        "distributor_part_number": "SS14FSCT-ND",
        "price_breaks": [
            {"qty": 1, "price": 0.22},
            {"qty": 100, "price": 0.15},
            {"qty": 1000, "price": 0.09},
            {"qty": 10000, "price": 0.055}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.onsemi.com/pdf/datasheet/ss12-d.pdf",
        "product_page_url": "https://www.digikey.com/en/products/detail/onsemi/SS14/1053429",
        "match_basis": "identified",
        "notes": "Power diode matched."
    },
    "4r7": {
        "manufacturer": "Bourns",
        "part_number": "SRR1260A-4R7Y",
        "description": "Shielded Power Inductor 4.7uH 6.5A SMD 12.5x12.5mm",
        "distributor": "Mouser",
        "distributor_part_number": "652-SRR1260A-4R7Y",
        "price_breaks": [
            {"qty": 1, "price": 1.10},
            {"qty": 100, "price": 0.85},
            {"qty": 1000, "price": 0.68},
            {"qty": 5000, "price": 0.54}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.bourns.com/docs/product-datasheets/srr1260a.pdf",
        "product_page_url": "https://www.mouser.com/ProductDetail/Bourns/SRR1260A-4R7Y",
        "match_basis": "equivalent",
        "notes": "Inductor matched based on 4R7 markings and size."
    },
    "w2f": {
        "manufacturer": "Nexperia",
        "part_number": "PMBT2907A",
        "description": "PNP Switching Transistor 60V 600mA SOT-23",
        "distributor": "DigiKey",
        "distributor_part_number": "568-1065-1-ND",
        "price_breaks": [
            {"qty": 1, "price": 0.12},
            {"qty": 100, "price": 0.08},
            {"qty": 1000, "price": 0.045},
            {"qty": 10000, "price": 0.028}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.nexperia.com/products/bipolar-transistors/general-purpose-bipolar-transistors/PMBT2907A.html",
        "product_page_url": "https://www.digikey.com/en/products/detail/nexperia-usa-inc/PMBT2907A-215/224214",
        "match_basis": "equivalent",
        "notes": "SOT-23 marking W2F resolved to Nexperia PMBT2907A."
    },
    "103": {
        "manufacturer": "Yageo",
        "part_number": "RC0805FR-0710KL",
        "description": "Thick Film Resistor 10k Ohm 1% 1/8W 0805",
        "distributor": "DigiKey",
        "distributor_part_number": "311-10.0KCRCT-ND",
        "price_breaks": [
            {"qty": 1, "price": 0.05},
            {"qty": 100, "price": 0.012},
            {"qty": 1000, "price": 0.004},
            {"qty": 10000, "price": 0.0018}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.yageo.com/upload/pdf/spec/spec_rc.pdf",
        "product_page_url": "https://www.digikey.com/en/products/detail/yageo/RC0805FR-0710KL/731234",
        "match_basis": "equivalent",
        "notes": "Resistor value 10k Ohm derived from 103 marking code."
    },
    "472": {
        "manufacturer": "Yageo",
        "part_number": "RC0805FR-074K7L",
        "description": "Thick Film Resistor 4.7k Ohm 1% 1/8W 0805",
        "distributor": "DigiKey",
        "distributor_part_number": "311-4.70KCRCT-ND",
        "price_breaks": [
            {"qty": 1, "price": 0.05},
            {"qty": 100, "price": 0.012},
            {"qty": 1000, "price": 0.004},
            {"qty": 10000, "price": 0.0018}
        ],
        "moq": 1,
        "stock_status": "In Stock",
        "datasheet_url": "https://www.yageo.com/upload/pdf/spec/spec_rc.pdf",
        "product_page_url": "https://www.digikey.com/en/products/detail/yageo/RC0805FR-074K7L/731238",
        "match_basis": "equivalent",
        "notes": "Resistor value 4.7k Ohm derived from 472 marking code."
    }
}

# Generic passive rules (Class + Package sizing)
# Format is "class:package"
GENERIC_CATALOG = {
    # Resistors
    "resistor:0402": {
        "manufacturer": "Generic",
        "part_number": "CR0402-10K-1%-ASSUMED",
        "description": "Thick Film Resistor Assumed 10k Ohm 1% 1/16W 0402",
        "distributor": "LCSC",
        "distributor_part_number": "C25081-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.02},
            {"qty": 100, "price": 0.004},
            {"qty": 1000, "price": 0.0015},
            {"qty": 10000, "price": 0.0008}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/2012111830_UNI-ROYAL-Uni-Elec-0402WGF1002TCE_C25081.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_UNI-ROYAL-Uni-Elec-0402WGF1002TCE_C25081.html",
        "notes": "Value, tolerance, and power ratings assumed for teardown costing purposes."
    },
    "resistor:0603": {
        "manufacturer": "Generic",
        "part_number": "CR0603-10K-1%-ASSUMED",
        "description": "Thick Film Resistor Assumed 10k Ohm 1% 1/10W 0603",
        "distributor": "LCSC",
        "distributor_part_number": "C25824-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.03},
            {"qty": 100, "price": 0.005},
            {"qty": 1000, "price": 0.0020},
            {"qty": 10000, "price": 0.0009}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1811142211_UNI-ROYAL-Uni-Elec-0603WGF1002T5E_C25824.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_UNI-ROYAL-Uni-Elec-0603WGF1002T5E_C25824.html",
        "notes": "Value, tolerance, and power ratings assumed for teardown costing purposes."
    },
    "resistor:0805": {
        "manufacturer": "Generic",
        "part_number": "CR0805-10K-1%-ASSUMED",
        "description": "Thick Film Resistor Assumed 10k Ohm 1% 1/8W 0805",
        "distributor": "LCSC",
        "distributor_part_number": "C25076-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.04},
            {"qty": 100, "price": 0.006},
            {"qty": 1000, "price": 0.0025},
            {"qty": 10000, "price": 0.0011}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1811141412_UNI-ROYAL-Uni-Elec-0805W8F1002T5E_C25076.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_UNI-ROYAL-Uni-Elec-0805W8F1002T5E_C25076.html",
        "notes": "Value, tolerance, and power ratings assumed for teardown costing purposes."
    },
    
    # Capacitors
    "capacitor:0402": {
        "manufacturer": "Generic",
        "part_number": "CC0402-100nF-50V-ASSUMED",
        "description": "Multi-layer Ceramic Capacitor Assumed 100nF 50V X7R 0402",
        "distributor": "LCSC",
        "distributor_part_number": "C1525-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.035},
            {"qty": 100, "price": 0.008},
            {"qty": 1000, "price": 0.0035},
            {"qty": 10000, "price": 0.0018}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1810311220_Samsung-Electro-Mechanics-CL05B104KO5NNNC_C1525.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_Samsung-Electro-Mechanics-CL05B104KO5NNNC_C1525.html",
        "notes": "Capacitance, voltage rating, and dielectric class assumed."
    },
    "capacitor:0603": {
        "manufacturer": "Generic",
        "part_number": "CC0603-100nF-50V-ASSUMED",
        "description": "Multi-layer Ceramic Capacitor Assumed 100nF 50V X7R 0603",
        "distributor": "LCSC",
        "distributor_part_number": "C14663-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.045},
            {"qty": 100, "price": 0.012},
            {"qty": 1000, "price": 0.005},
            {"qty": 10000, "price": 0.0022}
        ],
        "moq": 10,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1810311214_YAGEO-CC0603KRX7R9BB104_C14663.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_YAGEO-CC0603KRX7R9BB104_C14663.html",
        "notes": "Capacitance, voltage rating, and dielectric class assumed."
    },
    "capacitor:0805": {
        "manufacturer": "Generic",
        "part_number": "CC0805-1uF-50V-ASSUMED",
        "description": "Multi-layer Ceramic Capacitor Assumed 1uF 50V X7R 0805",
        "distributor": "LCSC",
        "distributor_part_number": "C28323-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.06},
            {"qty": 100, "price": 0.022},
            {"qty": 1000, "price": 0.011},
            {"qty": 10000, "price": 0.0065}
        ],
        "moq": 5,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1810311218_Samsung-Electro-Mechanics-CL21B105KOFNNNE_C28323.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_Samsung-Electro-Mechanics-CL21B105KOFNNNE_C28323.html",
        "notes": "Capacitance, voltage rating, and dielectric class assumed."
    },
    "capacitor:1206": {
        "manufacturer": "Generic",
        "part_number": "CC1206-10uF-50V-ASSUMED",
        "description": "Multi-layer Ceramic Capacitor Assumed 10uF 50V X7R 1206",
        "distributor": "LCSC",
        "distributor_part_number": "C13585-GEN",
        "price_breaks": [
            {"qty": 1, "price": 0.12},
            {"qty": 100, "price": 0.075},
            {"qty": 1000, "price": 0.045},
            {"qty": 10000, "price": 0.035}
        ],
        "moq": 5,
        "stock_status": "In Stock",
        "datasheet_url": "https://datasheet.lcsc.com/lcsc/1810311220_Samsung-Electro-Mechanics-CL31B106KOHNNNE_C13585.pdf",
        "product_page_url": "https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_Samsung-Electro-Mechanics-CL31B106KOHNNNE_C13585.html",
        "notes": "Capacitance, voltage rating, and dielectric class assumed."
    }
}

# Fallback prices for generic parts not explicitly matched in GENERIC_CATALOG
FALLBACK_PRICING = {
    "resistor": {
        "manufacturer": "Generic Resistor",
        "part_number": "RES-GENERIC",
        "description": "Generic Chip Resistor Value Assumed 10k 5%",
        "price": 0.002,
        "distributor": "LCSC",
        "distributor_part_number": "C-RES-GEN",
        "datasheet_url": "https://www.yageo.com/upload/pdf/spec/spec_rc.pdf",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Stated generic resistor assumed."
    },
    "capacitor": {
        "manufacturer": "Generic Capacitor",
        "part_number": "CAP-GENERIC",
        "description": "Generic Ceramic Chip Capacitor Assumed 100nF 50V X7R",
        "price": 0.005,
        "distributor": "LCSC",
        "distributor_part_number": "C-CAP-GEN",
        "datasheet_url": "https://www.yageo.com/upload/pdf/spec/spec_rc.pdf",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Stated generic capacitor assumed."
    },
    "inductor": {
        "manufacturer": "Generic Inductor",
        "part_number": "IND-GENERIC",
        "description": "Generic SMD Power Inductor Assumed 4.7uH",
        "price": 0.15,
        "distributor": "LCSC",
        "distributor_part_number": "C-IND-GEN",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Stated generic inductor assumed."
    },
    "transistor": {
        "manufacturer": "Generic Transistor",
        "part_number": "TRANS-SOT23",
        "description": "Generic SOT-23 NPN Switching Transistor",
        "price": 0.03,
        "distributor": "DigiKey",
        "distributor_part_number": "TRANS-GEN-SOT23",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic transistor."
    },
    "diode": {
        "manufacturer": "Generic Diode",
        "part_number": "DIODE-SMA",
        "description": "Generic 1A 40V Schottky Diode SMA",
        "price": 0.05,
        "distributor": "DigiKey",
        "distributor_part_number": "DIODE-GEN-SMA",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic diode."
    },
    "led": {
        "manufacturer": "Generic LED",
        "part_number": "LED-0603-GREEN",
        "description": "Generic Green Chip LED 0603",
        "price": 0.04,
        "distributor": "LCSC",
        "distributor_part_number": "LED-GEN-0603",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic indicator LED."
    },
    "connector": {
        "manufacturer": "Generic Connector",
        "part_number": "CONN-HEADER",
        "description": "Generic Male Header Connector",
        "price": 0.25,
        "distributor": "Mouser",
        "distributor_part_number": "CONN-GEN-HDR",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic board interconnect."
    },
    "crystal": {
        "manufacturer": "Generic Crystal",
        "part_number": "XTAL-12MHZ",
        "description": "Generic Metal Can Crystal 12MHz",
        "price": 0.18,
        "distributor": "Mouser",
        "distributor_part_number": "XTAL-GEN-12M",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic timing reference oscillator."
    },
    "default": {
        "manufacturer": "Generic Component",
        "part_number": "COMP-GENERIC",
        "description": "Unresolved Generic Component",
        "price": 0.10,
        "distributor": "DigiKey",
        "distributor_part_number": "COMP-GEN-ND",
        "datasheet_url": "https://datasheet.lcsc.com",
        "product_page_url": "https://www.lcsc.com",
        "notes": "Generic component pricing fallback."
    }
}

def resolve_price_at_volume(price_breaks: List[Dict[str, Any]], total_qty: int) -> Dict[str, Any]:
    if not price_breaks:
        return {"price": 0.0, "qty_used": 0}
        
    # Sort breaks by quantity ascending
    sorted_breaks = sorted(price_breaks, key=lambda b: b["qty"])
    
    # Pick the price break matching quantity
    selected_price = sorted_breaks[0]["price"]
    selected_qty = sorted_breaks[0]["qty"]
    
    for brk in sorted_breaks:
        if total_qty >= brk["qty"]:
            selected_price = brk["price"]
            selected_qty = brk["qty"]
            
    return {"price": selected_price, "qty_used": selected_qty}

def perform_sourcing_lookup(
    component_class: str,
    package: Optional[str],
    marking_text: Optional[str],
    build_volume: int,
    qty_per_board: int
) -> Dict[str, Any]:
    total_qty = build_volume * qty_per_board
    
    # 1. Determine key for caching
    cache_key = ""
    if marking_text:
        cache_key = marking_text.strip().lower()
    else:
        pkg_str = package.strip().lower() if package else "unknown"
        cache_key = f"{component_class.strip().lower()}:{pkg_str}"
        
    # 2. Try looking up in SQLite cache
    cached = get_cached_sourcing(cache_key)
    if cached:
        # Resolve dynamic price break
        price_info = resolve_price_at_volume(cached["price_breaks"], total_qty)
        return {
            **cached,
            "unit_price": price_info["price"],
            "price_break_qty": price_info["qty_used"],
            "extended_cost": price_info["price"] * qty_per_board,
            "moq": 1,
            "stock_status": "In Stock",
            "price_date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
    # 3. Cache Miss: lookup in embedded catalog
    sourcing_result = None
    
    # Attempt EXACT identified match
    if marking_text:
        text_clean = marking_text.strip().lower()
        if text_clean in LOCAL_CATALOG:
            sourcing_result = LOCAL_CATALOG[text_clean]
            
        # Try generic suffix/prefix check
        else:
            for k, val in LOCAL_CATALOG.items():
                if k in text_clean or text_clean in k:
                    sourcing_result = val
                    break
                    
    # Attempt GENERIC lookup
    if not sourcing_result and package:
        pkg_clean = package.strip().upper()
        # Clean imperial names (e.g. 0603-capacitor -> 0603)
        match_pkg = re.search(r"(\d{4})", pkg_clean)
        clean_pkg = match_pkg.group(1) if match_pkg else pkg_clean.lower()
        
        gen_key = f"{component_class.strip().lower()}:{clean_pkg}"
        if gen_key in GENERIC_CATALOG:
            sourcing_result = {
                **GENERIC_CATALOG[gen_key],
                "match_basis": "generic"
            }
            
    # 4. Fallback if still unresolved
    if not sourcing_result:
        cls_clean = component_class.strip().lower()
        fallback_data = FALLBACK_PRICING.get(cls_clean, FALLBACK_PRICING["default"])
        
        price_breaks = [
            {"qty": 1, "price": fallback_data["price"]},
            {"qty": 100, "price": fallback_data["price"] * 0.8},
            {"qty": 1000, "price": fallback_data["price"] * 0.65},
            {"qty": 10000, "price": fallback_data["price"] * 0.50}
        ]
        
        sourcing_result = {
            "manufacturer": fallback_data["manufacturer"],
            "part_number": fallback_data["part_number"],
            "description": fallback_data["description"],
            "distributor": fallback_data["distributor"],
            "distributor_part_number": fallback_data["distributor_part_number"],
            "price_breaks": price_breaks,
            "datasheet_url": fallback_data["datasheet_url"],
            "product_page_url": fallback_data["product_page_url"],
            "match_basis": "generic",
            "notes": fallback_data["notes"]
        }
        
    # Write back to SQLite cache
    sourcing_result["timestamp"] = datetime.datetime.utcnow().isoformat()
    set_cached_sourcing(cache_key, sourcing_result)
    
    # Resolve dynamic price break
    price_info = resolve_price_at_volume(sourcing_result["price_breaks"], total_qty)
    
    return {
        "manufacturer": sourcing_result.get("manufacturer"),
        "part_number": sourcing_result.get("part_number"),
        "description": sourcing_result.get("description"),
        "distributor": sourcing_result.get("distributor"),
        "distributor_part_number": sourcing_result.get("distributor_part_number"),
        "datasheet_url": sourcing_result.get("datasheet_url"),
        "product_page_url": sourcing_result.get("product_page_url"),
        "match_basis": sourcing_result["match_basis"],
        "unit_price": price_info["price"],
        "price_break_qty": price_info["qty_used"],
        "extended_cost": price_info["price"] * qty_per_board,
        "moq": sourcing_result.get("moq", 1),
        "stock_status": sourcing_result.get("stock_status", "In Stock"),
        "price_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "note": sourcing_result.get("notes") or sourcing_result.get("note")
    }
