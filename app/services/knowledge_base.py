"""
Farming knowledge base loader.
Seeds ChromaDB with curated agricultural knowledge documents
covering crops, soil, pests, weather, and market information.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from loguru import logger

from app.core.rag_pipeline import get_rag_pipeline

# ---------------------------------------------------------------------------
# Curated knowledge documents (embedded in code so the app works out-of-box)
# ---------------------------------------------------------------------------
FARMING_KNOWLEDGE: List[dict] = [
    # ── CROP RECOMMENDATIONS ────────────────────────────────────────────────
    {
        "content": (
            "Kharif crops are sown in June-July with the onset of monsoon and harvested "
            "in October-November. Major Kharif crops include: Rice (paddy), Maize, Sorghum "
            "(Jowar), Pearl Millet (Bajra), Finger Millet (Ragi), Cotton, Groundnut, Soybean, "
            "Sugarcane, Turmeric, and Ginger. For best yield, ensure proper drainage and "
            "monsoon-ready soil preparation. Apply basal fertilizer (NPK 10:26:26) before sowing."
        ),
        "source": "ICAR Crop Calendar",
        "category": "crop",
        "season": "kharif",
    },
    {
        "content": (
            "Rabi crops are sown in October-November after monsoon and harvested in "
            "March-April. Major Rabi crops: Wheat, Mustard (Canola), Chickpea (Gram), "
            "Lentil (Masoor), Barley, Peas, Sunflower. Rabi crops rely on residual moisture "
            "and winter rains. Wheat requires 4–5 irrigations. Apply urea top-dressing "
            "at tillering stage (21–25 days after sowing)."
        ),
        "source": "ICAR Crop Calendar",
        "category": "crop",
        "season": "rabi",
    },
    {
        "content": (
            "Zaid crops (summer crops) are grown from March to June between Rabi and Kharif. "
            "Main Zaid crops: Watermelon, Muskmelon, Cucumber, Bitter Gourd, Ridge Gourd, "
            "Moong Dal (Green gram), Fodder crops. Require warm weather and irrigation. "
            "These are short-duration crops ideal for market income between main seasons."
        ),
        "source": "ICAR Crop Calendar",
        "category": "crop",
        "season": "zaid",
    },
    {
        "content": (
            "Crop rotation guide: Rotating crops prevents soil nutrient depletion and breaks "
            "pest cycles. Recommended rotations:\n"
            "1. Rice → Wheat → Moong (most common in Indo-Gangetic plains)\n"
            "2. Cotton → Wheat → Groundnut\n"
            "3. Sugarcane → Wheat → Maize\n"
            "4. Soybean → Wheat (nitrogen-fixing legume improves soil)\n"
            "Avoid growing the same crop family (e.g., all cereals) consecutively."
        ),
        "source": "State Agriculture Department Guidelines",
        "category": "crop",
    },
    {
        "content": (
            "Vegetable farming calendar for India:\n"
            "• Tomato: Sow June-July (Kharif) or Oct-Nov (Rabi). Spacing 60x45 cm. "
            "Requires staking. Susceptible to early blight and leaf curl virus.\n"
            "• Onion: Kharif sowing May-June; Rabi sowing Oct-Dec. Needs well-drained loamy soil.\n"
            "• Potato: Rabi crop, sown Oct-Nov. Requires cool temperature 15–20°C.\n"
            "• Chilli: Sow June-July for Kharif. Rich in Vitamin C; high market value.\n"
            "All vegetables need soil pH 6.0–7.0 and regular fertigation."
        ),
        "source": "ICAR Horticulture Division",
        "category": "crop",
    },
    # ── SOIL HEALTH ─────────────────────────────────────────────────────────
    {
        "content": (
            "Soil testing is essential before sowing. Contact your nearest Soil Testing "
            "Laboratory or Krishi Vigyan Kendra (KVK) for free/subsidized tests. "
            "Key soil parameters: pH (ideal 6.0–7.5), Nitrogen (N), Phosphorus (P), "
            "Potassium (K), Organic Carbon, Micronutrients (Zinc, Boron, Iron). "
            "Soil Health Cards issued under PM Soil Health Card Scheme provide "
            "crop-specific fertilizer recommendations."
        ),
        "source": "PM Soil Health Card Scheme",
        "category": "soil",
    },
    {
        "content": (
            "Improving soil organic matter:\n"
            "• Apply Farm Yard Manure (FYM) at 10–15 tonnes/hectare.\n"
            "• Use vermicompost at 2–3 tonnes/hectare for micronutrients.\n"
            "• Green manuring with Dhaincha (Sesbania) or Sunhemp before Kharif.\n"
            "• Mulching with crop residues reduces evaporation and adds organic matter.\n"
            "• Avoid burning crop stubble — incorporate into soil instead.\n"
            "Organic carbon above 0.75% indicates healthy, fertile soil."
        ),
        "source": "ICAR Soil Science Division",
        "category": "soil",
    },
    {
        "content": (
            "Fertilizer application guide (per hectare):\n"
            "• Rice: N-120, P-60, K-40 kg/ha. Split N in 3 doses.\n"
            "• Wheat: N-120, P-60, K-40 kg/ha. Apply Zinc sulfate 25 kg/ha if deficient.\n"
            "• Maize: N-120, P-60, K-40 kg/ha + Zinc 5 kg/ha.\n"
            "• Cotton: N-120, P-60, K-60 kg/ha. Apply boron for boll development.\n"
            "• Soybean: Rhizobium seed treatment reduces N requirement by 25 kg/ha.\n"
            "Always apply basal dose at sowing and top-dress at critical growth stages."
        ),
        "source": "ICAR Fertilizer Use Efficiency Guidelines",
        "category": "soil",
    },
    # ── PEST & DISEASE MANAGEMENT ───────────────────────────────────────────
    {
        "content": (
            "Integrated Pest Management (IPM) principles:\n"
            "1. Monitor fields regularly (twice a week during critical periods).\n"
            "2. Use Economic Threshold Level (ETL) to decide on spraying.\n"
            "3. Prefer cultural controls: crop rotation, resistant varieties, field sanitation.\n"
            "4. Biological controls: Trichogramma cards for stem borers, NPV for Helicoverpa.\n"
            "5. Chemical control: last resort. Use recommended pesticides at correct dose.\n"
            "6. Follow pre-harvest intervals (PHI) strictly for food safety."
        ),
        "source": "Central IPM Centre, DPPQ&S",
        "category": "pest",
    },
    {
        "content": (
            "Common rice pests and management:\n"
            "• Stem borer: Yellow stem borer and striped stem borer cause 'dead hearts' and "
            "'white ears'. Use Chlorpyrifos 20EC @ 1500 ml/ha or Pheromone traps.\n"
            "• Brown Planthopper (BPH): Causes 'hopper burn'. Avoid excessive N. "
            "Use Buprofezin 25SC @ 625 ml/ha.\n"
            "• Blast disease (fungal): Apply Tricyclazole 75WP @ 300g/ha at boot leaf stage.\n"
            "• Bacterial Leaf Blight: Use resistant varieties. Avoid flood irrigation."
        ),
        "source": "CRRI Rice Pest Management",
        "category": "pest",
        "crop": "rice",
    },
    {
        "content": (
            "Common wheat and rabi crop pests:\n"
            "• Aphids on wheat: Apply Dimethoate 30EC @ 500 ml/ha or Imidacloprid.\n"
            "• Rust diseases (yellow, brown, black): Use Propiconazole 25EC @ 500 ml/ha.\n"
            "• Termites: Apply Chlorpyrifos 20EC in irrigation water at sowing.\n"
            "• Rodents: Use zinc phosphide bait in bait stations (not open fields).\n"
            "Monitor for powdery mildew in mustard; apply Wettable Sulfur if needed."
        ),
        "source": "ICAR-IIWBR Wheat Pest Guide",
        "category": "pest",
        "crop": "wheat",
    },
    {
        "content": (
            "Organic/bio-pesticide options approved in India:\n"
            "• Neem-based products (Azadirachtin 1500 ppm): Effective against aphids, "
            "thrips, mites. Apply @ 2–5 ml/litre water. Safe for beneficial insects.\n"
            "• Spinosad: For Fruit borers and leaf miners.\n"
            "• Beauveria bassiana: For whitefly and thrips in protected cultivation.\n"
            "• Trichoderma viride/harzianum: For soil-borne fungal diseases (Fusarium, Pythium).\n"
            "• Pheromone traps: Monitoring and mass trapping of moth pests."
        ),
        "source": "CIBRC Approved Bio-Pesticides List",
        "category": "pest",
    },
    # ── WEATHER & IRRIGATION ────────────────────────────────────────────────
    {
        "content": (
            "Irrigation scheduling guide:\n"
            "• Critical irrigation stages for wheat: Crown Root Initiation (21 DAS), "
            "Tillering (40 DAS), Jointing (60 DAS), Flowering (80 DAS), Grain filling (100 DAS).\n"
            "• Rice requires continuous flooding or Alternate Wetting and Drying (AWD) technique "
            "which saves 20–30% water.\n"
            "• Drip irrigation for vegetables reduces water use by 40–60% and improves quality.\n"
            "• Avoid irrigation during noon in summer to reduce evaporation losses."
        ),
        "source": "ICAR Water Technology Centre",
        "category": "weather",
    },
    {
        "content": (
            "Weather-based crop advisory:\n"
            "• High humidity (>85%) + temperature 25–30°C: High disease risk. "
            "Apply preventive fungicide spray.\n"
            "• Strong winds (>40 km/h): Avoid pesticide spraying; risk of drift.\n"
            "• Cold wave (<10°C): Cover nurseries with polythene. Irrigate to prevent frost damage.\n"
            "• Heat wave (>42°C): Irrigate crops immediately. Apply kaolin clay spray on fruit crops.\n"
            "• Pre-monsoon showers: Good time for dry sowing of Kharif crops."
        ),
        "source": "IMD Agromet Advisory Services",
        "category": "weather",
    },
    # ── MARKET & GOVERNMENT SCHEMES ─────────────────────────────────────────
    {
        "content": (
            "Minimum Support Price (MSP) for major crops 2024-25 (per quintal):\n"
            "• Paddy (Common): ₹2,300 | Fine: ₹2,320\n"
            "• Wheat: ₹2,275\n"
            "• Maize: ₹2,090\n"
            "• Soybean: ₹4,892\n"
            "• Cotton (Medium staple): ₹7,121 | Long staple: ₹7,521\n"
            "• Groundnut: ₹6,783\n"
            "• Mustard: ₹5,650\n"
            "• Gram (Chickpea): ₹5,440\n"
            "Sell at government procurement centres to receive MSP. Register on PM-KISAN portal."
        ),
        "source": "CACP - Commission for Agricultural Costs and Prices 2024-25",
        "category": "market",
    },
    {
        "content": (
            "Government schemes for farmers in India:\n"
            "• PM-KISAN: ₹6,000/year direct income support. Register at pmkisan.gov.in.\n"
            "• PM Fasal Bima Yojana (PMFBY): Crop insurance at 2% premium for Kharif, "
            "1.5% for Rabi. Enroll through your bank or CSC centre.\n"
            "• Kisan Credit Card (KCC): Short-term crop loans at 4% interest rate.\n"
            "• PM Krishi Sinchai Yojana: Subsidies for drip/sprinkler irrigation.\n"
            "• Soil Health Card: Free soil testing every 2 years.\n"
            "• National Agriculture Market (e-NAM): Online mandi platform for better prices."
        ),
        "source": "Ministry of Agriculture & Farmers Welfare",
        "category": "market",
    },
    {
        "content": (
            "e-NAM (National Agriculture Market) guide:\n"
            "e-NAM is a pan-India electronic trading platform connecting APMC mandis. "
            "Benefits: transparent price discovery, direct payment to bank account, "
            "access to buyers across India.\n"
            "How to join: Register at enam.gov.in with Aadhaar, bank account, and land records.\n"
            "Over 1,300 mandis across 22 states are integrated on e-NAM.\n"
            "Assay (quality testing) labs available at major mandis ensure fair pricing."
        ),
        "source": "SFAC - e-NAM Portal",
        "category": "market",
    },
    # ── SMART FARMING TECHNOLOGY ─────────────────────────────────────────────
    {
        "content": (
            "Precision agriculture technologies available in India:\n"
            "• Drone spraying: DGCA-approved agricultural drones for pesticide/fertilizer "
            "application. Saves 30–35% chemical use. Subsidy available under sub-mission on "
            "Agricultural Mechanization.\n"
            "• Remote sensing & satellite imagery: Free NDVI maps via Fasal app and "
            "Kisan Suvidha app (Govt of India).\n"
            "• Soil moisture sensors: IoT-based sensors for smart irrigation scheduling.\n"
            "• Variable Rate Technology (VRT): Apply inputs based on soil variability maps."
        ),
        "source": "ICAR-NAARM Technology Division",
        "category": "general",
    },
    {
        "content": (
            "Post-harvest management to reduce losses:\n"
            "• Cereal storage: Use HDPE bags or hermetic storage bags (Purdue Improved "
            "Cowpea Storage). Maintain moisture content below 12–14%.\n"
            "• Cold storage for fruits/vegetables: Pre-cooling within 2 hours of harvest "
            "extends shelf life 5–10x.\n"
            "• Warehouse Receipt System: Store crops in accredited warehouses and get loans "
            "against stored produce (Negotiable Warehouse Receipt).\n"
            "• Post-harvest losses in India: 15–20% for cereals, 25–30% for fruits/vegetables. "
            "Proper storage can save ₹90,000 crore annually."
        ),
        "source": "ICAR-CIPHET Post-Harvest Management",
        "category": "general",
    },
]


def load_knowledge_base() -> int:
    """
    Ingest all farming knowledge documents into ChromaDB.
    Returns the number of chunks stored.
    """
    rag = get_rag_pipeline()

    # Convert to LangChain Documents
    documents: List[Document] = []
    for item in FARMING_KNOWLEDGE:
        doc = Document(
            page_content=item["content"],
            metadata={
                "source": item.get("source", "Smart Farming Knowledge Base"),
                "category": item.get("category", "general"),
                "season": item.get("season", ""),
                "crop": item.get("crop", ""),
            },
        )
        documents.append(doc)

    # Also load any external .txt/.json files from data/knowledge_base/
    kb_dir = Path("data/knowledge_base")
    if kb_dir.exists():
        for txt_file in kb_dir.glob("*.txt"):
            try:
                content = txt_file.read_text(encoding="utf-8")
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"source": txt_file.name, "category": "general"},
                    )
                )
                logger.info(f"Loaded external knowledge file: {txt_file.name}")
            except Exception as exc:
                logger.warning(f"Could not read {txt_file}: {exc}")

    total = rag.ingest_documents(documents)
    logger.info(f"Knowledge base loaded: {total} chunks in ChromaDB.")
    return total
