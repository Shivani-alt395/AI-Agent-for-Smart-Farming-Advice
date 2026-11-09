"""
Market price service — fetches mandi (APMC) prices.
Primary: data.gov.in API (free with API key)
Fallback: curated state-wise indicative mandi prices (2024-25)
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import MandiPrice


# ── State name normalisation map ─────────────────────────────────────────────
STATE_ALIASES: Dict[str, str] = {
    "ap": "Andhra Pradesh", "andhra": "Andhra Pradesh", "andhra pradesh": "Andhra Pradesh",
    "ka": "Karnataka", "karnataka": "Karnataka", "kk": "Karnataka",
    "mh": "Maharashtra", "maharashtra": "Maharashtra",
    "up": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh",
    "mp": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh",
    "rj": "Rajasthan", "rajasthan": "Rajasthan",
    "hr": "Haryana", "haryana": "Haryana",
    "pb": "Punjab", "punjab": "Punjab",
    "tn": "Tamil Nadu", "tamilnadu": "Tamil Nadu", "tamil nadu": "Tamil Nadu",
    "ts": "Telangana", "telangana": "Telangana",
    "gj": "Gujarat", "gujarat": "Gujarat",
    "wb": "West Bengal", "west bengal": "West Bengal",
    "br": "Bihar", "bihar": "Bihar",
    "od": "Odisha", "odia": "Odisha", "odisha": "Odisha",
    "kl": "Kerala", "kerala": "Kerala",
    "hp": "Himachal Pradesh", "himachal": "Himachal Pradesh", "himachal pradesh": "Himachal Pradesh",
    "jk": "Jammu and Kashmir", "jammu": "Jammu and Kashmir",
    "as": "Assam", "assam": "Assam",
    "cg": "Chhattisgarh", "chhattisgarh": "Chhattisgarh",
    "jh": "Jharkhand", "jharkhand": "Jharkhand",
    "uk": "Uttarakhand", "uttarakhand": "Uttarakhand",
}


# ── Rich static mandi data (state-wise, 2024-25) ─────────────────────────────
STATIC_PRICES: List[Dict[str, Any]] = [
    # ── National MSP & Wholesale (All India) ──
    {"commodity": "Wheat",          "min": 2015,  "max": 2275,  "modal": 2275,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Paddy (Rice)",   "min": 2100,  "max": 2300,  "modal": 2300,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Maize",          "min": 1900,  "max": 2090,  "modal": 2090,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Soybean",        "min": 4500,  "max": 4892,  "modal": 4892,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Cotton",         "min": 6600,  "max": 7121,  "modal": 7121,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Groundnut",      "min": 6000,  "max": 6783,  "modal": 6783,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Mustard",        "min": 5200,  "max": 5650,  "modal": 5650,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Gram (Chickpea)","min": 5100,  "max": 5440,  "modal": 5440,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Arhar (Tur Dal)","min": 6300,  "max": 7000,  "modal": 7000,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Moong Dal",      "min": 7500,  "max": 8682,  "modal": 8682,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Urad Dal",       "min": 6800,  "max": 7400,  "modal": 7000,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Masoor Dal",     "min": 5500,  "max": 6000,  "modal": 5800,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Jowar",          "min": 2900,  "max": 3180,  "modal": 3180,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Bajra",          "min": 2250,  "max": 2500,  "modal": 2500,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Ragi",           "min": 3800,  "max": 4290,  "modal": 4290,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Sesame",         "min": 8635,  "max": 9267,  "modal": 9267,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Sunflower",      "min": 6760,  "max": 7280,  "modal": 7280,  "market": "National MSP",         "state": "All India",      "district": ""},
    {"commodity": "Sugarcane",      "min": 315,   "max": 340,   "modal": 340,   "market": "FRP 2024-25",          "state": "All India",      "district": ""},
    # ── National Wholesale (processed commodities not covered by MSP) ──
    {"commodity": "Sugar (Refined)","min": 3800,  "max": 4200,  "modal": 4000,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Cashew",         "min": 80000, "max": 130000,"modal": 100000,"market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Coconut",        "min": 1200,  "max": 2500,  "modal": 1800,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Black Pepper",   "min": 40000, "max": 60000, "modal": 50000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Cardamom",       "min": 90000, "max": 150000,"modal": 120000,"market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Garlic",         "min": 3000,  "max": 8000,  "modal": 5000,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Ginger",         "min": 3000,  "max": 8000,  "modal": 5500,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Coriander",      "min": 5000,  "max": 9000,  "modal": 7000,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Fenugreek",      "min": 5000,  "max": 7000,  "modal": 6000,  "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Tobacco",        "min": 18000, "max": 28000, "modal": 22000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Tea",            "min": 15000, "max": 30000, "modal": 22000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Coffee",         "min": 10000, "max": 20000, "modal": 15000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Walnut",         "min": 60000, "max": 90000, "modal": 75000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Almond",         "min": 70000, "max": 110000,"modal": 90000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Turmeric",       "min": 8000,  "max": 18000, "modal": 13000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    {"commodity": "Chilli (Red)",   "min": 8000,  "max": 20000, "modal": 14000, "market": "National Wholesale",   "state": "All India",      "district": ""},
    # ── Maharashtra ──
    {"commodity": "Tomato",         "min": 800,   "max": 2200,  "modal": 1500,  "market": "Nashik APMC",          "state": "Maharashtra",    "district": "Nashik"},
    {"commodity": "Onion",          "min": 600,   "max": 1800,  "modal": 1200,  "market": "Lasalgaon APMC",       "state": "Maharashtra",    "district": "Nashik"},
    {"commodity": "Grapes",         "min": 3000,  "max": 8000,  "modal": 5000,  "market": "Sangli APMC",          "state": "Maharashtra",    "district": "Sangli"},
    {"commodity": "Pomegranate",    "min": 4000,  "max": 12000, "modal": 7000,  "market": "Solapur APMC",         "state": "Maharashtra",    "district": "Solapur"},
    {"commodity": "Banana",         "min": 1200,  "max": 2500,  "modal": 1800,  "market": "Jalgaon APMC",         "state": "Maharashtra",    "district": "Jalgaon"},
    {"commodity": "Mango",          "min": 8000,  "max": 20000, "modal": 12000, "market": "Ratnagiri APMC",       "state": "Maharashtra",    "district": "Ratnagiri"},
    {"commodity": "Wheat",          "min": 2100,  "max": 2400,  "modal": 2250,  "market": "Pune APMC",            "state": "Maharashtra",    "district": "Pune"},
    {"commodity": "Cotton",         "min": 6800,  "max": 7500,  "modal": 7200,  "market": "Akola APMC",           "state": "Maharashtra",    "district": "Akola"},
    # ── Uttar Pradesh ──
    {"commodity": "Potato",         "min": 500,   "max": 1100,  "modal": 800,   "market": "Agra APMC",            "state": "Uttar Pradesh",  "district": "Agra"},
    {"commodity": "Wheat",          "min": 2050,  "max": 2300,  "modal": 2200,  "market": "Lucknow APMC",         "state": "Uttar Pradesh",  "district": "Lucknow"},
    {"commodity": "Sugarcane",      "min": 350,   "max": 380,   "modal": 370,   "market": "Meerut APMC",          "state": "Uttar Pradesh",  "district": "Meerut"},
    {"commodity": "Paddy (Rice)",   "min": 2100,  "max": 2400,  "modal": 2250,  "market": "Gorakhpur APMC",       "state": "Uttar Pradesh",  "district": "Gorakhpur"},
    {"commodity": "Onion",          "min": 700,   "max": 1500,  "modal": 1100,  "market": "Kanpur APMC",          "state": "Uttar Pradesh",  "district": "Kanpur"},
    # ── Karnataka ──
    {"commodity": "Tomato",         "min": 600,   "max": 2000,  "modal": 1300,  "market": "Kolar APMC",           "state": "Karnataka",      "district": "Kolar"},
    {"commodity": "Onion",          "min": 700,   "max": 1600,  "modal": 1200,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Potato",         "min": 800,   "max": 1500,  "modal": 1100,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Ragi",           "min": 3200,  "max": 3800,  "modal": 3500,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Areca Nut",      "min": 30000, "max": 50000, "modal": 40000, "market": "Shimoga APMC",         "state": "Karnataka",      "district": "Shimoga"},
    {"commodity": "Coffee",         "min": 12000, "max": 18000, "modal": 15000, "market": "Chikmagalur APMC",     "state": "Karnataka",      "district": "Chikmagalur"},
    {"commodity": "Maize",          "min": 1900,  "max": 2200,  "modal": 2050,  "market": "Davangere APMC",       "state": "Karnataka",      "district": "Davangere"},
    {"commodity": "Sugarcane",      "min": 2800,  "max": 3200,  "modal": 3000,  "market": "Belgaum APMC",         "state": "Karnataka",      "district": "Belgaum"},
    {"commodity": "Garlic",         "min": 4000,  "max": 9000,  "modal": 6000,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Ginger",         "min": 3500,  "max": 8000,  "modal": 5500,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Coconut",        "min": 1200,  "max": 2200,  "modal": 1700,  "market": "Tumkur APMC",          "state": "Karnataka",      "district": "Tumkur"},
    {"commodity": "Cashew",         "min": 70000, "max": 120000,"modal": 90000, "market": "Mangalore APMC",       "state": "Karnataka",      "district": "Dakshina Kannada"},
    {"commodity": "Black Pepper",   "min": 45000, "max": 65000, "modal": 55000, "market": "Mangalore APMC",       "state": "Karnataka",      "district": "Dakshina Kannada"},
    {"commodity": "Groundnut",      "min": 5500,  "max": 6800,  "modal": 6200,  "market": "Bellary APMC",         "state": "Karnataka",      "district": "Bellary"},
    {"commodity": "Wheat",          "min": 2100,  "max": 2350,  "modal": 2250,  "market": "Bangalore APMC",       "state": "Karnataka",      "district": "Bengaluru"},
    {"commodity": "Jowar",          "min": 2800,  "max": 3200,  "modal": 3000,  "market": "Bijapur APMC",         "state": "Karnataka",      "district": "Bijapur"},
    # ── Andhra Pradesh / Telangana ──
    {"commodity": "Chilli (Red)",   "min": 8000,  "max": 18000, "modal": 12000, "market": "Guntur APMC",          "state": "Andhra Pradesh", "district": "Guntur"},
    {"commodity": "Turmeric",       "min": 10000, "max": 18000, "modal": 14000, "market": "Nizamabad APMC",       "state": "Telangana",      "district": "Nizamabad"},
    {"commodity": "Paddy (Rice)",   "min": 2100,  "max": 2350,  "modal": 2250,  "market": "Nellore APMC",         "state": "Andhra Pradesh", "district": "Nellore"},
    {"commodity": "Cotton",         "min": 6700,  "max": 7300,  "modal": 7000,  "market": "Warangal APMC",        "state": "Telangana",      "district": "Warangal"},
    # ── Rajasthan ──
    {"commodity": "Mustard",        "min": 5100,  "max": 5800,  "modal": 5500,  "market": "Alwar APMC",           "state": "Rajasthan",      "district": "Alwar"},
    {"commodity": "Cumin",          "min": 18000, "max": 28000, "modal": 22000, "market": "Jodhpur APMC",         "state": "Rajasthan",      "district": "Jodhpur"},
    {"commodity": "Gram (Chickpea)","min": 5200,  "max": 5700,  "modal": 5500,  "market": "Jaipur APMC",          "state": "Rajasthan",      "district": "Jaipur"},
    # ── Punjab / Haryana ──
    {"commodity": "Wheat",          "min": 2100,  "max": 2350,  "modal": 2275,  "market": "Ludhiana APMC",        "state": "Punjab",         "district": "Ludhiana"},
    {"commodity": "Paddy (Rice)",   "min": 2200,  "max": 2400,  "modal": 2300,  "market": "Amritsar APMC",        "state": "Punjab",         "district": "Amritsar"},
    {"commodity": "Wheat",          "min": 2100,  "max": 2350,  "modal": 2275,  "market": "Karnal APMC",          "state": "Haryana",        "district": "Karnal"},
    {"commodity": "Sugarcane",      "min": 360,   "max": 390,   "modal": 375,   "market": "Panipat APMC",         "state": "Haryana",        "district": "Panipat"},
    # ── Madhya Pradesh ──
    {"commodity": "Soybean",        "min": 4600,  "max": 5000,  "modal": 4800,  "market": "Indore APMC",          "state": "Madhya Pradesh", "district": "Indore"},
    {"commodity": "Gram (Chickpea)","min": 5200,  "max": 5700,  "modal": 5400,  "market": "Ujjain APMC",          "state": "Madhya Pradesh", "district": "Ujjain"},
    {"commodity": "Wheat",          "min": 2000,  "max": 2300,  "modal": 2200,  "market": "Bhopal APMC",          "state": "Madhya Pradesh", "district": "Bhopal"},
    # ── Gujarat ──
    {"commodity": "Groundnut",      "min": 5800,  "max": 6900,  "modal": 6400,  "market": "Rajkot APMC",          "state": "Gujarat",        "district": "Rajkot"},
    {"commodity": "Cotton",         "min": 6700,  "max": 7300,  "modal": 7000,  "market": "Ahmedabad APMC",       "state": "Gujarat",        "district": "Ahmedabad"},
    {"commodity": "Castor",         "min": 5500,  "max": 6500,  "modal": 6000,  "market": "Mehsana APMC",         "state": "Gujarat",        "district": "Mehsana"},
    # ── Tamil Nadu ──
    {"commodity": "Paddy (Rice)",   "min": 2100,  "max": 2400,  "modal": 2250,  "market": "Thanjavur APMC",       "state": "Tamil Nadu",     "district": "Thanjavur"},
    {"commodity": "Banana",         "min": 1500,  "max": 3000,  "modal": 2000,  "market": "Trichy APMC",          "state": "Tamil Nadu",     "district": "Tiruchirappalli"},
    {"commodity": "Coconut",        "min": 1200,  "max": 2000,  "modal": 1600,  "market": "Coimbatore APMC",      "state": "Tamil Nadu",     "district": "Coimbatore"},
    # ── West Bengal ──
    {"commodity": "Paddy (Rice)",   "min": 2000,  "max": 2300,  "modal": 2200,  "market": "Burdwan APMC",         "state": "West Bengal",    "district": "Burdwan"},
    {"commodity": "Potato",         "min": 600,   "max": 1200,  "modal": 900,   "market": "Hooghly APMC",         "state": "West Bengal",    "district": "Hooghly"},
    {"commodity": "Jute",           "min": 4500,  "max": 5500,  "modal": 5000,  "market": "Murshidabad APMC",     "state": "West Bengal",    "district": "Murshidabad"},
    # ── Bihar ──
    {"commodity": "Paddy (Rice)",   "min": 2000,  "max": 2300,  "modal": 2150,  "market": "Patna APMC",           "state": "Bihar",          "district": "Patna"},
    {"commodity": "Sugarcane",      "min": 340,   "max": 375,   "modal": 360,   "market": "Patna APMC",           "state": "Bihar",          "district": "Patna"},
    {"commodity": "Maize",          "min": 1800,  "max": 2100,  "modal": 1950,  "market": "Muzaffarpur APMC",     "state": "Bihar",          "district": "Muzaffarpur"},
    {"commodity": "Potato",         "min": 500,   "max": 1000,  "modal": 750,   "market": "Nalanda APMC",         "state": "Bihar",          "district": "Nalanda"},
    {"commodity": "Wheat",          "min": 2000,  "max": 2275,  "modal": 2200,  "market": "Patna APMC",           "state": "Bihar",          "district": "Patna"},
    {"commodity": "Onion",          "min": 600,   "max": 1400,  "modal": 1000,  "market": "Patna APMC",           "state": "Bihar",          "district": "Patna"},
    {"commodity": "Tomato",         "min": 500,   "max": 1800,  "modal": 1200,  "market": "Patna APMC",           "state": "Bihar",          "district": "Patna"},
    # ── Maharashtra (additional) ──
    {"commodity": "Garlic",         "min": 3000,  "max": 8000,  "modal": 5500,  "market": "Pune APMC",            "state": "Maharashtra",    "district": "Pune"},
    {"commodity": "Ginger",         "min": 2500,  "max": 7000,  "modal": 4500,  "market": "Mumbai APMC",          "state": "Maharashtra",    "district": "Mumbai"},
    {"commodity": "Onion",          "min": 500,   "max": 2200,  "modal": 1400,  "market": "Pune APMC",            "state": "Maharashtra",    "district": "Pune"},
    {"commodity": "Cashew",         "min": 75000, "max": 125000,"modal": 95000, "market": "Konkan APMC",          "state": "Maharashtra",    "district": "Ratnagiri"},
    {"commodity": "Jowar",          "min": 2800,  "max": 3200,  "modal": 3000,  "market": "Solapur APMC",         "state": "Maharashtra",    "district": "Solapur"},
    # ── Andhra Pradesh / Telangana (additional) ──
    {"commodity": "Onion",          "min": 600,   "max": 1500,  "modal": 1100,  "market": "Kurnool APMC",         "state": "Andhra Pradesh", "district": "Kurnool"},
    {"commodity": "Tomato",         "min": 500,   "max": 2000,  "modal": 1300,  "market": "Madanapalle APMC",     "state": "Andhra Pradesh", "district": "Chittoor"},
    {"commodity": "Banana",         "min": 1000,  "max": 2500,  "modal": 1700,  "market": "Nuziveedu APMC",       "state": "Andhra Pradesh", "district": "Krishna"},
    {"commodity": "Cashew",         "min": 75000, "max": 120000,"modal": 95000, "market": "Srikakulam APMC",      "state": "Andhra Pradesh", "district": "Srikakulam"},
    {"commodity": "Garlic",         "min": 3000,  "max": 8000,  "modal": 5500,  "market": "Hyderabad APMC",       "state": "Telangana",      "district": "Hyderabad"},
    {"commodity": "Ginger",         "min": 3000,  "max": 7500,  "modal": 5000,  "market": "Hyderabad APMC",       "state": "Telangana",      "district": "Hyderabad"},
    # ── Rajasthan (additional) ──
    {"commodity": "Garlic",         "min": 3500,  "max": 9000,  "modal": 6000,  "market": "Kota APMC",            "state": "Rajasthan",      "district": "Kota"},
    {"commodity": "Coriander",      "min": 5000,  "max": 9000,  "modal": 7000,  "market": "Ramganj Mandi APMC",   "state": "Rajasthan",      "district": "Kota"},
    {"commodity": "Fenugreek",      "min": 5000,  "max": 7000,  "modal": 6000,  "market": "Nagaur APMC",          "state": "Rajasthan",      "district": "Nagaur"},
    # ── Kerala ──
    {"commodity": "Coconut",        "min": 1500,  "max": 2500,  "modal": 2000,  "market": "Thrissur APMC",        "state": "Kerala",         "district": "Thrissur"},
    {"commodity": "Black Pepper",   "min": 45000, "max": 65000, "modal": 55000, "market": "Perambra APMC",        "state": "Kerala",         "district": "Kozhikode"},
    {"commodity": "Cardamom",       "min": 90000, "max": 150000,"modal": 120000,"market": "Kumily APMC",          "state": "Kerala",         "district": "Idukki"},
    {"commodity": "Cashew",         "min": 80000, "max": 130000,"modal": 105000,"market": "Kollam APMC",          "state": "Kerala",         "district": "Kollam"},
    {"commodity": "Banana",         "min": 1500,  "max": 3000,  "modal": 2200,  "market": "Thrissur APMC",        "state": "Kerala",         "district": "Thrissur"},
    {"commodity": "Ginger",         "min": 4000,  "max": 9000,  "modal": 6500,  "market": "Wayanad APMC",         "state": "Kerala",         "district": "Wayanad"},
    {"commodity": "Tea",            "min": 18000, "max": 32000, "modal": 25000, "market": "Munnar APMC",          "state": "Kerala",         "district": "Idukki"},
    {"commodity": "Coffee",         "min": 12000, "max": 20000, "modal": 16000, "market": "Wayanad APMC",         "state": "Kerala",         "district": "Wayanad"},
    # ── Himachal Pradesh ──
    {"commodity": "Apple",          "min": 5000,  "max": 15000, "modal": 9000,  "market": "Shimla APMC",          "state": "Himachal Pradesh","district": "Shimla"},
    {"commodity": "Garlic",         "min": 4000,  "max": 10000, "modal": 7000,  "market": "Solan APMC",           "state": "Himachal Pradesh","district": "Solan"},
    {"commodity": "Ginger",         "min": 3500,  "max": 8000,  "modal": 5500,  "market": "Kullu APMC",           "state": "Himachal Pradesh","district": "Kullu"},
    # ── Uttar Pradesh (additional) ──
    {"commodity": "Garlic",         "min": 3000,  "max": 8000,  "modal": 5500,  "market": "Agra APMC",            "state": "Uttar Pradesh",  "district": "Agra"},
    {"commodity": "Ginger",         "min": 2500,  "max": 7000,  "modal": 4500,  "market": "Lucknow APMC",         "state": "Uttar Pradesh",  "district": "Lucknow"},
    {"commodity": "Maize",          "min": 1800,  "max": 2100,  "modal": 1950,  "market": "Varanasi APMC",        "state": "Uttar Pradesh",  "district": "Varanasi"},
    {"commodity": "Tomato",         "min": 600,   "max": 2000,  "modal": 1300,  "market": "Lucknow APMC",         "state": "Uttar Pradesh",  "district": "Lucknow"},
]


def _normalise_state(raw: Optional[str]) -> Optional[str]:
    """Normalise various state name forms to canonical name."""
    if not raw:
        return None
    s = raw.strip().lower()
    # Try alias map first
    if s in STATE_ALIASES:
        return STATE_ALIASES[s]
    # Partial match
    for alias, canonical in STATE_ALIASES.items():
        if alias in s or s in alias:
            return canonical
    # Return capitalised version as-is for data.gov.in query
    return raw.strip().title()


class MarketService:
    """Fetch agricultural market/mandi prices."""

    def __init__(self):
        self._settings = get_settings()

    async def get_prices(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 15,
    ) -> List[MandiPrice]:
        """
        Fetch prices. Try live data.gov.in first, then state-aware static fallback.
        state can be a full name like "Karnataka" or a location string like "Nashik, Maharashtra"
        """
        # Extract state from a "district, state" string if needed
        resolved_state = state
        resolved_district = district
        if state and "," in state:
            parts = [p.strip() for p in state.split(",")]
            resolved_district = resolved_district or parts[0]
            resolved_state = parts[-1]

        canonical_state = _normalise_state(resolved_state)

        api_key = self._settings.data_gov_api_key
        if api_key and api_key != "your_data_gov_in_api_key_here":
            live = await self._fetch_live_prices(commodity, canonical_state, resolved_district, limit, api_key)
            if live:
                return live

        return self._get_static_prices(commodity, canonical_state, resolved_district, limit)

    async def _fetch_live_prices(
        self,
        commodity: Optional[str],
        state: Optional[str],
        district: Optional[str],
        limit: int,
        api_key: str,
    ) -> List[MandiPrice]:
        params: Dict[str, Any] = {
            "api-key": api_key,
            "format": "json",
            "limit": limit,
        }
        if commodity:
            params["filters[commodity]"] = commodity
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self._settings.data_gov_mandi_url, params=params)
                resp.raise_for_status()
                data = resp.json()
                records = data.get("records", [])
                prices = []
                for r in records:
                    prices.append(
                        MandiPrice(
                            commodity=r.get("commodity", "Unknown"),
                            market=r.get("market", "Unknown"),
                            state=r.get("state", "Unknown"),
                            min_price=float(r.get("min_price", 0)),
                            max_price=float(r.get("max_price", 0)),
                            modal_price=float(r.get("modal_price", 0)),
                            date=r.get("arrival_date", str(date.today())),
                        )
                    )
                logger.info(f"Fetched {len(prices)} live mandi prices (state={state}, district={district}).")
                return prices
        except Exception as exc:
            logger.warning(f"Live mandi API failed: {exc}")
            return []

    def _get_static_prices(
        self,
        commodity: Optional[str],
        state: Optional[str],
        district: Optional[str],
        limit: int,
    ) -> List[MandiPrice]:
        today = str(date.today())
        results = list(STATIC_PRICES)

        # Filter by commodity
        if commodity:
            c_low = commodity.lower()
            results = [r for r in results if c_low in r["commodity"].lower()]

        # Filter by state — prefer exact state match, then All India
        if state:
            s_low = state.lower()
            state_matches  = [r for r in results if s_low in r["state"].lower()]
            all_india      = [r for r in results if r["state"] == "All India"]
            # If we have state-specific data, put them first; append MSP at end
            state_only     = [r for r in state_matches if r["state"] != "All India"]
            results = state_only + [r for r in all_india if r not in state_matches]
        else:
            # No state — sort: All India MSP first
            results = sorted(results, key=lambda r: 0 if r["state"] == "All India" else 1)

        # Filter by district (optional refinement on top of state)
        if district:
            d_low = district.lower()
            district_matches = [r for r in results if d_low in r["district"].lower()]
            if district_matches:
                others = [r for r in results if r not in district_matches]
                results = district_matches + others

        return [
            MandiPrice(
                commodity=r["commodity"],
                market=r["market"],
                state=r["state"],
                min_price=float(r["min"]),
                max_price=float(r["max"]),
                modal_price=float(r["modal"]),
                date=today,
            )
            for r in results[:limit]
        ]

    def format_prices_as_text(self, prices: List[MandiPrice]) -> str:
        if not prices:
            return "No price data available."
        lines = ["**Current Mandi/Market Prices (₹ per Quintal):**\n"]
        for p in prices:
            lines.append(
                f"• {p.commodity}: ₹{p.min_price:,.0f}–₹{p.max_price:,.0f} "
                f"(Modal: ₹{p.modal_price:,.0f}) — {p.market}, {p.state}"
            )
        return "\n".join(lines)
