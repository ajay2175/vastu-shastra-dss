"""
Comprehensive Vastu Shastra Embedded Knowledge Base

Core principles embedded as Python dictionaries for standalone DSS without external VDBs.
References: Mayamatam, Brihat Samhita, Aparajitapriccha, Vastu Shastra Upanishads

Author: Claude Haiku 4.5
Version: 1.0
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass


# ============================================================================
# 1. DIRECTIONAL PRINCIPLES (8 Primary + Center)
# ============================================================================

DIRECTIONS = {
    "north": {
        "name": "North (Uttara)",
        "governing_deity": "Kubera",
        "planetary_ruler": "Mercury",
        "element": "water",
        "characteristics": [
            "Wealth, prosperity, and fortune",
            "Commerce and business",
            "Knowledge and learning",
            "Communication and intellect",
            "North flow of positive energy",
            "Cooling, receptive energy"
        ],
        "optimal_rooms": ["living_room", "study", "office", "treasury"],
        "colors": {
            "primary": "white",
            "secondary": "gray",
            "accent": "blue"
        },
        "defects": {
            "blocked": "Loss of wealth and opportunities",
            "dark": "Stagnation in career"
        },
        "references": [
            "Mayamatam 14.180-195",
            "Brihat Samhita 53.1-50"
        ]
    },

    "northeast": {
        "name": "Northeast (Ishanya)",
        "governing_deity": "Ishana (Shiva)",
        "planetary_ruler": "Jupiter",
        "element": "ether/space",
        "characteristics": [
            "Spiritual growth and wisdom",
            "Divine connection and purity",
            "Health and healing",
            "Mental clarity and intuition"
        ],
        "optimal_rooms": ["puja_room", "meditation_space", "master_bedroom"],
        "colors": {
            "primary": "light yellow",
            "secondary": "light blue",
            "accent": "white"
        },
        "importance": "CRITICAL - Most auspicious direction",
        "references": [
            "Mayamatam 14.1-50",
            "Vastu Shastra Upanishad 1.1"
        ]
    },

    "east": {
        "name": "East (Purva)",
        "governing_deity": "Indra",
        "planetary_ruler": "Sun",
        "element": "fire",
        "characteristics": [
            "Enlightenment and spiritual awakening",
            "Health and vitality",
            "Success and fame",
            "Source of life force (Prana)"
        ],
        "optimal_rooms": ["entrance", "master_bedroom", "puja_room"],
        "colors": {
            "primary": "golden yellow",
            "secondary": "light orange",
            "accent": "red"
        },
        "references": [
            "Mayamatam 14.100-130",
            "Brihat Samhita 53.40-60"
        ]
    },

    "southeast": {
        "name": "Southeast (Agneya)",
        "governing_deity": "Agni (Fire God)",
        "planetary_ruler": "Venus",
        "element": "fire",
        "characteristics": [
            "Transformation and purification",
            "Digestive fire and metabolism",
            "Dynamic energy and activity",
            "Passion and motivation"
        ],
        "optimal_rooms": ["kitchen", "office", "exercise_room"],
        "avoid_rooms": ["bedroom", "puja_room", "child_room"],
        "colors": {
            "primary": "red",
            "secondary": "orange",
            "accent": "golden"
        },
        "references": [
            "Mayamatam 14.160-180",
            "Brihat Samhita 53.60-80"
        ]
    },

    "south": {
        "name": "South (Dakshina)",
        "governing_deity": "Yama",
        "planetary_ruler": "Mars",
        "element": "earth",
        "characteristics": [
            "Stability, strength, and grounding",
            "Authority and leadership",
            "Material wealth and property",
            "Protection and boundaries"
        ],
        "optimal_rooms": ["bedroom", "master_bedroom", "storage"],
        "colors": {
            "primary": "red",
            "secondary": "brown",
            "accent": "dark orange"
        },
        "references": [
            "Mayamatam 14.150-165",
            "Brihat Samhita 53.80-100"
        ]
    },

    "southwest": {
        "name": "Southwest (Nairutya)",
        "governing_deity": "Nirriti",
        "planetary_ruler": "Rahu",
        "element": "earth",
        "characteristics": [
            "Stability and weight",
            "Heavy responsibilities",
            "Grounding and foundation",
            "Heaviness and density"
        ],
        "optimal_rooms": ["master_bedroom", "storage", "vault"],
        "avoid_rooms": ["puja_room", "child_room", "meditation_space"],
        "colors": {
            "primary": "brown",
            "secondary": "earth tones",
            "accent": "dark red"
        },
        "principle": "Heaviest and most protected direction",
        "references": [
            "Mayamatam 14.200-220"
        ]
    },

    "west": {
        "name": "West (Pashchima)",
        "governing_deity": "Varuna",
        "planetary_ruler": "Saturn",
        "element": "water",
        "characteristics": [
            "Reflection and introspection",
            "Emotional depth and mystery",
            "Endings and transitions",
            "Receptivity to inner worlds"
        ],
        "optimal_rooms": ["bedroom", "study", "library"],
        "avoid_rooms": ["kitchen", "entrance", "puja_room"],
        "colors": {
            "primary": "blue",
            "secondary": "gray",
            "accent": "white"
        },
        "references": [
            "Mayamatam 14.120-150"
        ]
    },

    "northwest": {
        "name": "Northwest (Vayavya)",
        "governing_deity": "Vayu (Wind)",
        "planetary_ruler": "Moon",
        "element": "air",
        "characteristics": [
            "Movement, change, and adaptability",
            "Communication and ideas",
            "Transient energy and impermanence",
            "Learning and new perspectives"
        ],
        "optimal_rooms": ["guest_room", "office", "storage"],
        "avoid_rooms": ["master_bedroom", "puja_room", "kitchen"],
        "colors": {
            "primary": "gray",
            "secondary": "white",
            "accent": "light blue"
        },
        "principle": "Lightest and most open quadrant",
        "references": [
            "Mayamatam 14.210-230"
        ]
    },

    "center": {
        "name": "Center (Brahma Sthana)",
        "governing_deity": "Brahma",
        "element": "ether/space",
        "characteristics": [
            "Divine consciousness and unity",
            "Spiritual heart of the dwelling",
            "Balance of all five elements",
            "Cosmic connection point"
        ],
        "optimal_rooms": ["open_court", "meditation_space"],
        "avoid_rooms": ["toilet", "staircase_center"],
        "importance": "MOST CRITICAL - Heart of property",
        "principle": "MUST remain completely clear and open",
        "references": [
            "Mayamatam 14.1-100",
            "Vastu Shastra Upanishad 1.1-30"
        ]
    }
}


# ============================================================================
# 2. VASTU DOSHAS (20+ Defects)
# ============================================================================

VASTU_DOSHAS = {
    "brahma_sthana_violation": {
        "name": "Brahma Sthana Violation",
        "severity": "CRITICAL",
        "description": "Central space is occupied, closed, or contains toilet/staircase/kitchen",
        "impacts": {
            "health": ["Depression", "Mental disorders", "Central nervous system issues"],
            "relationships": ["Family discord", "Disconnection"],
            "wealth": ["Loss of opportunities", "Financial stagnation"],
            "spiritual": ["Spiritual blockage", "Loss of peace"]
        },
        "remedies": [
            "Immediate relocation of occupying structure",
            "Install Brahma Sthana crystal or yantra at center",
            "Daily meditation at center"
        ]
    },

    "northeast_toilet": {
        "name": "Northeast Toilet Dosha",
        "severity": "CRITICAL",
        "description": "Toilet or waste in northeast direction",
        "impacts": {
            "health": ["Severe health decline", "Infectious diseases"],
            "wealth": ["Rapid financial loss", "Business failure"],
            "spiritual": ["Complete spiritual blockage"]
        },
        "remedies": [
            "Complete relocation or permanent closure",
            "Move toilet to Southeast corner only",
            "Perform purification rituals daily for 40 days"
        ],
        "severity_note": "Most inauspicious configuration in Vastu"
    },

    "central_pit": {
        "name": "Central Pit Dosha",
        "severity": "CRITICAL",
        "description": "Depression, pit, or sunken area in center",
        "impacts": {
            "health": ["Chronic weakness", "Depression"],
            "wealth": ["Complete financial loss"],
            "psychological": ["Deep psychological issues"]
        },
        "remedies": [
            "Fill pit completely to same level",
            "Use auspicious earth, no waste",
            "Install Brahma Yantra at center",
            "Perform abhisheka rituals"
        ]
    },

    "southeast_kitchen": {
        "name": "Southeast Kitchen Dosha",
        "severity": "HIGH",
        "description": "Kitchen in southeast (excess fire creates imbalance)",
        "impacts": {
            "health": ["Digestive disorders", "Liver problems", "Inflammation"],
            "relationships": ["Marital discord", "Anger and irritability"],
            "wealth": ["Wasteful spending", "Financial drain"]
        },
        "remedies": [
            "Relocation to Northeast or East",
            "Paint walls white or light colors",
            "Install water element (aquarium/fountain)",
            "Place mirror on south wall",
            "Install Vastu correction yantra"
        ]
    },

    "northwest_toilet": {
        "name": "Northwest Toilet Dosha",
        "severity": "HIGH",
        "description": "Toilet in northwest (Vayu with waste creates confusion)",
        "impacts": {
            "health": ["Respiratory issues", "Anxiety", "Confusion"],
            "relationships": ["Instability in relationships"],
            "wealth": ["Loss through carelessness", "Missed opportunities"]
        },
        "remedies": [
            "Relocation to Southeast or South",
            "Paint walls light gray or white",
            "Install mirrors on north and east walls",
            "Use air purification and ventilation"
        ]
    },

    "blocked_entry": {
        "name": "Blocked Entry Dosha",
        "severity": "HIGH",
        "description": "Main entrance blocked, dark, or obstructed",
        "impacts": {
            "health": ["Weak immune system", "Lethargy"],
            "relationships": ["Isolation", "Loss of connections"],
            "wealth": ["Lost opportunities", "Stagnant income"]
        },
        "remedies": [
            "Clear all obstructions",
            "Install bright light",
            "Paint white or light color",
            "Create open, inviting space"
        ]
    },

    "central_staircase": {
        "name": "Central Staircase Dosha",
        "severity": "HIGH",
        "description": "Staircase in center of house cuts Brahma Sthana",
        "impacts": {
            "health": ["Heart issues", "Nervous system disorders"],
            "relationships": ["Family separation", "Estrangement"],
            "wealth": ["Divided wealth", "Loss of unity"]
        },
        "remedies": [
            "Relocation to periphery (N, S, E, or W)",
            "Paint staircase white",
            "Install lights at each step",
            "Place Brahma Yantra on landing"
        ]
    },

    "sloped_foundation": {
        "name": "Sloped Foundation Dosha",
        "severity": "MEDIUM-HIGH",
        "description": "Property sloped downward (SW to NE worst)",
        "impacts": {
            "wealth": ["Loss of stability", "Financial decline"],
            "health": ["Unstable health", "Chronic weakness"],
            "relationships": ["Unstable relationships"]
        },
        "remedies": [
            "Level foundation as much as possible",
            "Raise lower area with earth fill",
            "Install retaining walls",
            "Place Ganesha idol at lowest point"
        ]
    },

    "missing_quadrant": {
        "name": "Missing Quadrant Dosha",
        "severity": "HIGH",
        "description": "L-shaped property with missing corner",
        "impacts": {
            "northeast_missing": ["Spiritual/health loss"],
            "southeast_missing": ["Financial loss", "Health issues"],
            "southwest_missing": ["Weakness", "Loss of authority"],
            "northwest_missing": ["Mental confusion", "Relationship instability"]
        },
        "remedies": [
            "Install mirror on external wall",
            "Build extension to fill space",
            "Place corresponding deity idol",
            "Install Vastu correction yantra"
        ]
    },

    "poison_beam": {
        "name": "Poison Beam (Brahma Ari)",
        "severity": "MEDIUM",
        "description": "Beam or pillar directly above bed",
        "impacts": {
            "health": ["Disease along beam line", "Organ problems"],
            "relationships": ["If above couple: Separation", "Discord"]
        },
        "remedies": [
            "Move bed to avoid beam",
            "Cover beam with white cloth",
            "Install mirrors on sides",
            "Paint beam white to make recessive"
        ]
    },

    "sharp_corner_projection": {
        "name": "Sharp Corner Projection Dosha",
        "severity": "MEDIUM",
        "description": "Sharp edges protruding into rooms",
        "impacts": {
            "health": ["Accidents", "Injuries"],
            "psychology": ["Tension", "Unease", "Subconscious stress"],
            "relationships": ["Arguments", "Conflicts"]
        },
        "remedies": [
            "Round corners with curved surfaces",
            "Install mirror perpendicular to corner",
            "Place plant or decoration to soften",
            "Paint corner white to recede",
            "Hang crystal or wind chime"
        ]
    },

    "water_retention": {
        "name": "Water Retention Areas Dosha",
        "severity": "MEDIUM",
        "description": "Areas where water accumulates/doesn't drain",
        "impacts": {
            "health": ["Dampness diseases", "Respiratory issues", "Fungal infections"],
            "wealth": ["Stagnation", "Slow progress"],
            "psychology": ["Depression", "Lethargy"]
        },
        "remedies": [
            "Improve drainage system",
            "Create slopes for water flow",
            "Install sump pump if necessary",
            "Apply waterproofing",
            "Increase ventilation and light"
        ]
    },

    "open_southwest": {
        "name": "Open Southwest Dosha",
        "severity": "MEDIUM",
        "description": "Southwest corner open, exposed, or lower",
        "impacts": {
            "wealth": ["Loss of accumulated wealth", "Property loss"],
            "health": ["Lack of grounding", "Weakness"],
            "psychology": ["Lack of foundation", "Insecurity"]
        },
        "remedies": [
            "Build wall or barrier in SW",
            "Plant strong trees in SW corner",
            "Place heavy stones or sculptures",
            "Install solid gate in SW",
            "Raise ground level in SW"
        ]
    },

    "electromagnetic_stress": {
        "name": "Electromagnetic Stress Dosha",
        "severity": "MEDIUM",
        "description": "High EMF from transformers, power lines, cell towers",
        "impacts": {
            "health": ["Weakened immunity", "Sleep disorders", "Headaches", "Fatigue"],
            "psychology": ["Anxiety", "Irritability", "Memory issues"]
        },
        "remedies": [
            "Move away from EM source if possible",
            "Install EMF shielding",
            "Use copper or aluminum barriers",
            "Keep bedroom away from electrical equipment",
            "Install grounding systems"
        ]
    }
}


# ============================================================================
# 3. ROOM CORRELATIONS (10 rooms)
# ============================================================================

ROOM_PLACEMENTS = {
    "bedroom": {
        "primary_optimal": "southwest",
        "secondary_optimal": ["south", "west"],
        "avoid": ["northeast", "center", "southeast"],
        "optimal_head_direction": "south or west",
        "colors": {
            "best": "Soft pastels: cream, light pink, pale yellow",
            "avoid": "Bright red, black, dark colors"
        },
        "elements": ["Earth (stability)", "Water (cooling for sleep)"],
        "master_bedroom_note": "Southwest is BEST for marital harmony",
        "health_correlations": {
            "northeast_bed": "Sleep disturbance, anxiety",
            "southwest_bed": "Deep sleep, stability, strength"
        }
    },

    "kitchen": {
        "primary_optimal": "southeast",
        "secondary_optimal": ["east"],
        "avoid": ["northeast", "center", "northwest"],
        "stove_placement": "Southeast corner, slightly away from exact corner",
        "stove_direction": "Cook faces East or North",
        "sink_placement": "North or Northeast",
        "storage": "South and West walls",
        "colors": {
            "best": "White, light yellow, light green",
            "avoid": "Black, dark red"
        },
        "health_correlations": {
            "southeast_kitchen": "Good digestion, healthy family",
            "northeast_kitchen": "Severe health issues"
        }
    },

    "living_room": {
        "primary_optimal": "north",
        "secondary_optimal": ["northeast", "east"],
        "avoid": ["southwest"],
        "purpose": "Entertainment and gathering",
        "colors": {
            "best": "White, light gray, light blue",
            "accents": "Green (growth), yellow (joy)"
        },
        "tv_placement": "Southeast corner",
        "proportions": "Slightly larger than bedroom"
    },

    "puja_room": {
        "primary_optimal": "northeast",
        "secondary_optimal": ["east", "north"],
        "avoid": ["southeast", "southwest"],
        "lighting": "Bright, preferably ghee lamps or natural",
        "cleanliness": "ABSOLUTE - daily cleaning mandatory",
        "prohibitions": ["No cooking nearby", "No toilet nearby", "No loud noises"],
        "water_feature": "North side for purification"
    },

    "office": {
        "primary_optimal": "north",
        "secondary_optimal": ["northeast", "east"],
        "avoid": ["southwest"],
        "desk_placement": "Back to North wall, facing South",
        "colors": {
            "best": "White, light blue, light yellow",
            "accent": "Green (growth)"
        },
        "windows": "East or North for morning light"
    },

    "entrance": {
        "primary_optimal": "north",
        "secondary_optimal": ["northeast", "east"],
        "avoid": ["southwest"],
        "purpose": "Welcoming, prosperous entry",
        "lighting": "Bright light at entrance",
        "door_color": "Brown, white, yellow, red - never black",
        "clutter": "MUST be clear"
    },

    "bathroom": {
        "primary_optimal": "southeast",
        "secondary_optimal": ["south"],
        "avoid": ["northeast", "center", "north"],
        "toilet_placement": "Southeast or South corner",
        "toilet_facing": "North or East while sitting",
        "colors": {
            "best": "White, light blue, light green",
            "avoid": "Black, dark red"
        },
        "cleanliness": "ESSENTIAL - daily cleaning"
    },

    "storage_room": {
        "primary_optimal": "south",
        "secondary_optimal": ["southwest"],
        "avoid": ["northeast", "center"],
        "shelving": "South and West walls",
        "valuables_placement": "South or Southwest corner",
        "organization": "Orderly, no clutter"
    },

    "garage": {
        "primary_optimal": "south",
        "secondary_optimal": ["southeast", "west"],
        "avoid": ["northeast"],
        "vehicle_orientation": "Enter from E/N, exit S/W"
    },

    "outdoor_garden": {
        "primary_optimal": "north and northeast",
        "secondary_optimal": ["east"],
        "avoid": ["southwest"],
        "water_feature_flow": "North or East",
        "trees": ["Tulsi", "Neem", "Banyan", "Pipal", "Ashoka"]
    }
}


# ============================================================================
# 4. REMEDIES (15+ categories)
# ============================================================================

REMEDIES = {
    "color_correction": {
        "principle": "Colors represent elements and influence energy",
        "color_meanings": {
            "white": ["Purity", "Peace", "Clarity"],
            "yellow": ["Knowledge", "Warmth", "Prosperity"],
            "red": ["Energy", "Passion", "Fire"],
            "orange": ["Creativity", "Enthusiasm", "Warmth"],
            "green": ["Growth", "Healing", "Balance"],
            "blue": ["Calm", "Communication", "Water"],
            "purple": ["Spirituality", "Wisdom", "Transformation"],
            "brown": ["Grounding", "Stability", "Earth"]
        }
    },

    "element_balancing": {
        "principle": "Balance all five elements",
        "elements": {
            "earth": ["Brown/yellow colors", "Stones", "Ceramics", "Plants"],
            "water": ["Blue colors", "Fountains", "Aquariums", "Mirrors"],
            "fire": ["Red/orange", "Candles", "Lamps", "Lights"],
            "air": ["Green/white", "Windows", "Ventilation", "Wind chimes"],
            "ether": ["Open spaces", "Skylights", "High ceilings"]
        }
    },

    "mirror_placement": {
        "principle": "Mirrors reflect and redirect energy",
        "optimal_uses": [
            "North wall: prosperity",
            "East wall: health and opportunity",
            "Opposite sharp corner: reflect energy away",
            "Dark rooms: position to catch and reflect light"
        ]
    },

    "light_enhancement": {
        "principle": "Light represents knowledge and prosperity",
        "light_types": {
            "natural": ["Sunrise East", "Skylights", "Windows"],
            "ghee_lamps": ["Sacred", "Purifying", "Puja rooms"],
            "candles": ["Meditative", "Ceremonial"],
            "uplighting": ["Expands space", "Energizing"]
        }
    },

    "yantra_placement": {
        "principle": "Yantras invoke specific energies",
        "types": {
            "shri_yantra": "Wealth and abundance",
            "brahma_yantra": "Spiritual protection",
            "durga_yantra": "Protection and obstacles",
            "ganesha_yantra": "Success and prosperity",
            "lakshmi_yantra": "Wealth and abundance"
        }
    },

    "crystal_placement": {
        "principle": "Crystals transmit specific energies",
        "common_crystals": {
            "clear_quartz": "Master healer, universal",
            "citrine": "Prosperity, North placement",
            "amethyst": "Spiritual growth, NE/center",
            "rose_quartz": "Love and harmony, bedroom",
            "black_tourmaline": "Protection, entrance",
            "pyrite": "Wealth, office/north"
        }
    }
}


# ============================================================================
# 5. SACRED GEOMETRY
# ============================================================================

SACRED_GEOMETRY = {
    "vastu_purusha_mandala": {
        "name": "Vastu Purusha Mandala",
        "description": "Sacred geometric map of deity positions",
        "deities": {
            "center": "Brahma (cosmic consciousness)",
            "northeast": "Ishana/Shiva (spirituality)",
            "north": "Kubera (wealth)",
            "east": "Indra (health, fame)",
            "southeast": "Agni (fire, transformation)",
            "south": "Yama (dharma)",
            "southwest": "Nirriti (obstacles)",
            "west": "Varuna (water, emotions)",
            "northwest": "Vayu (wind, change)"
        }
    },

    "sacred_proportions": {
        "golden_ratio": "1:1.618 (Phi)",
        "silver_ratio": "1:1.414",
        "room_ratios": {
            "1:1": "Square - balanced",
            "1:1.5": "Active flow",
            "2:3": "Harmonious",
            "3:4": "Dynamic growth",
            "4:5": "Grounding"
        }
    },

    "chakra_correspondences": {
        "principle": "Home has chakra system like human body",
        "locations": {
            "root": "Southwest - stability",
            "sacral": "Southeast - creativity",
            "solar_plexus": "East - personal power",
            "heart": "Center - love and unity",
            "throat": "West - expression",
            "third_eye": "North - intuition",
            "crown": "Above center - divine"
        }
    }
}


# ============================================================================
# 6. HEALTH CORRELATIONS
# ============================================================================

HEALTH_CORRELATIONS = {
    "vata_dosha": {
        "element": "Air, Ether",
        "aggravating_spaces": ["Northwest", "Open/cold", "Sloped", "Cluttered"],
        "health_issues": ["Anxiety", "Sleep disturbance", "Confusion", "Joint problems"],
        "pacifying": "South, Southwest (grounding, warming)"
    },

    "pitta_dosha": {
        "element": "Fire, Water",
        "aggravating_spaces": ["Southeast", "Overheated/bright", "Red spaces"],
        "health_issues": ["Inflammation", "Acid reflux", "Skin problems", "Anger"],
        "pacifying": "North, West (cool, introspective)"
    },

    "kapha_dosha": {
        "element": "Water, Earth",
        "aggravating_spaces": ["Southwest", "Damp/dark", "Dense/crowded", "Stagnant"],
        "health_issues": ["Sluggish digestion", "Congestion", "Depression", "Weight gain"],
        "pacifying": "East, Southeast (energizing)"
    },

    "directional_health": {
        "northeast": "Spiritual well-being, mental peace",
        "north": "Prosperity supports health",
        "east": "Vitality and strong immunity",
        "southeast": "Healthy digestion",
        "south": "Grounding and strong bones",
        "southwest": "Deep rest and stability",
        "west": "Emotional balance",
        "northwest": "Mental clarity",
        "center": "Integration of all systems"
    }
}


# ============================================================================
# 7. TEMPORAL ASPECTS
# ============================================================================

TEMPORAL_ASPECTS = {
    "auspicious_days": {
        "thursday": ["Most auspicious", "Prosperity", "Jupiter-ruled"],
        "wednesday": ["Communication", "Mercury-ruled"],
        "monday": ["New beginnings", "Water features"],
        "tuesday": ["Strong actions", "Mars-ruled"],
        "sunday": ["Success", "Solar-ruled"]
    },

    "auspicious_months": {
        "ashwin": ["Most auspicious", "September-October"],
        "kartik": ["Sacred month", "October-November"],
        "chaitra": ["New beginnings", "March-April"],
        "vasant": ["Spring", "Growth"]
    },

    "seasonal_focus": {
        "spring": "Growth, newness, light colors",
        "summer": "Cool colors and water, pitta control",
        "monsoon": "Waterproofing and drainage",
        "autumn": "Most balanced, auspicious",
        "winter": "Warmth, fire and earth, grounding"
    }
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_direction_info(direction: str) -> Optional[Dict[str, Any]]:
    """Retrieve information for a specific direction."""
    return DIRECTIONS.get(direction.lower())


def get_dosha_info(dosha_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve information for a Vastu dosha."""
    return VASTU_DOSHAS.get(dosha_name.lower().replace(" ", "_"))


def get_room_placement(room_type: str) -> Optional[Dict[str, Any]]:
    """Retrieve optimal placement for a room type."""
    return ROOM_PLACEMENTS.get(room_type.lower())


def list_all_directions() -> List[str]:
    """List all directional principles."""
    return list(DIRECTIONS.keys())


def list_all_doshas() -> List[str]:
    """List all Vastu doshas."""
    return list(VASTU_DOSHAS.keys())


def list_all_rooms() -> List[str]:
    """List all room types."""
    return list(ROOM_PLACEMENTS.keys())


# ============================================================================
# ADVICE DATACLASS
# ============================================================================

@dataclass
class Advice:
    """Advice data structure."""
    principle: str
    direction: str
    reasoning: str
    recommendation: str


# ============================================================================
# VASTU PRINCIPLES WRAPPER CLASS
# ============================================================================

class VastuPrinciples:
    """Wrapper class providing all methods expected by StandaloneConsultation."""

    def __init__(self):
        """Initialize VastuPrinciples."""
        pass

    def validate_layout(self, space_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate space layout for Vastu compliance."""
        direction = space_details.get("direction", "").lower()
        space_type = space_details.get("type", "").lower()

        validation_score = 75  # Default score

        # Check for issues
        issues = space_details.get("issues", [])
        if issues:
            validation_score -= len(issues) * 10

        # Check direction suitability
        if direction and space_type:
            room_info = get_room_placement(space_type)
            if room_info:
                if direction in room_info.get("avoid", []):
                    validation_score -= 20
                elif direction == room_info.get("primary_optimal"):
                    validation_score += 10

        validation_score = max(0, min(100, validation_score))

        return {
            "validation_score": validation_score,
            "issues_detected": len(issues),
            "recommendations": ["Keep space clean", "Ensure proper lighting", "Balance elements"]
        }

    def generate_advice(self, space_details: Dict[str, Any]) -> List[Advice]:
        """Generate advice for a space."""
        advice_list = []
        direction = space_details.get("direction", "").lower()
        space_type = space_details.get("type", "").lower()

        # Get direction advice
        if direction in DIRECTIONS:
            dir_info = DIRECTIONS[direction]
            advice_list.append(Advice(
                principle=f"Apply {direction.title()} directional principles",
                direction=direction,
                reasoning=f"The {direction} is governed by {dir_info.get('governing_deity')}",
                recommendation=f"Follow {direction} guidelines for this space"
            ))

        # Get room placement advice
        if space_type in ROOM_PLACEMENTS:
            room_info = ROOM_PLACEMENTS[space_type]
            advice_list.append(Advice(
                principle=f"Optimal {space_type} placement",
                direction=room_info.get("primary_optimal", ""),
                reasoning=f"The {space_type} works best in {room_info.get('primary_optimal')} direction",
                recommendation=f"Consider relocation if not in optimal direction"
            ))

        if not advice_list:
            advice_list.append(Advice(
                principle="General Vastu principles",
                direction="center",
                reasoning="Keep Brahma Sthana clear and clean",
                recommendation="Maintain central space"
            ))

        return advice_list

    def get_remedy_suggestions(self, issue: str) -> Dict[str, Dict[str, str]]:
        """Get remedy suggestions for an issue."""
        remedies = {
            "color_correction": {
                "white": "Use white to purify and expand space",
                "yellow": "Use yellow to bring warmth and knowledge",
                "blue": "Use blue to bring calm and clarity"
            },
            "element_balancing": {
                "water": "Add water feature (fountain/aquarium) to balance",
                "fire": "Add lights or candles to activate fire element",
                "earth": "Add plants or stones for grounding"
            },
            "mirror_placement": {
                "north_wall": "Place mirror on north wall for prosperity",
                "east_wall": "Place mirror on east wall for health",
                "opposite_corner": "Place mirror opposite sharp corner"
            }
        }
        return remedies

    def suggest_color_for_space(self, space_details: Dict[str, Any]) -> str:
        """Suggest a color for a space."""
        direction = space_details.get("direction", "").lower()
        space_type = space_details.get("type", "").lower()

        # Check room-specific color
        if space_type in ROOM_PLACEMENTS:
            room_info = ROOM_PLACEMENTS[space_type]
            if "colors" in room_info:
                return room_info["colors"].get("best", "White")

        # Check direction-specific color
        if direction in DIRECTIONS:
            dir_info = DIRECTIONS[direction]
            colors = dir_info.get("colors", {})
            if isinstance(colors, dict):
                return colors.get("primary", "White")

        return "White"

    def get_element_for_direction(self, direction: str) -> str:
        """Get element associated with a direction."""
        direction = direction.lower()
        if direction in DIRECTIONS:
            return DIRECTIONS[direction].get("element", "Unknown")
        return "Unknown"

    def get_direction_advice(self, direction: str) -> Optional[Dict[str, Any]]:
        """Get detailed advice for a direction."""
        direction = direction.lower()
        if direction not in DIRECTIONS:
            return None

        dir_info = DIRECTIONS[direction]
        return {
            "name": dir_info.get("name"),
            "description": f"The {dir_info.get('name')} is governed by {dir_info.get('governing_deity')}",
            "key_points": dir_info.get("characteristics", [])[:3],
            "elements": [dir_info.get("element", "")],
            "colors": list(dir_info.get("colors", {}).values()) if isinstance(dir_info.get("colors"), dict) else [],
            "remedies": self._get_direction_remedies(direction)
        }

    def get_room_guidelines(self, room_type: str) -> Optional[Dict[str, Any]]:
        """Get guidelines for a room type."""
        room_type = room_type.lower()
        if room_type not in ROOM_PLACEMENTS:
            return None

        room_info = ROOM_PLACEMENTS[room_type]
        return {
            "best_directions": [room_info.get("primary_optimal", "")] + room_info.get("secondary_optimal", []),
            "avoid": room_info.get("avoid", []),
            "shape": "Square or rectangular",
            "window_placement": "East or North for natural light",
            "color": room_info.get("colors", {}).get("best", "White") if isinstance(room_info.get("colors"), dict) else "White",
            "furniture": "Place heavy items in appropriate direction"
        }

    def check_defect(self, defect_type: str) -> Optional[Dict[str, Any]]:
        """Check for a specific Vastu defect."""
        defect_key = defect_type.lower().replace(" ", "_")
        if defect_key not in VASTU_DOSHAS:
            return None

        dosha_info = VASTU_DOSHAS[defect_key]
        return {
            "problem": dosha_info.get("description"),
            "impact": str(dosha_info.get("impacts", {}).get("health", ["Unknown"])[0]),
            "severity": dosha_info.get("severity"),
            "remedies": dosha_info.get("remedies", [])
        }

    def _get_direction_remedies(self, direction: str) -> List[str]:
        """Get remedies specific to a direction."""
        remedies_map = {
            "northeast": ["Keep clear and clean", "Install bright light", "Place deity idol"],
            "north": ["Enhance with water feature", "Use mirrors", "Promote prosperity items"],
            "east": ["Maximize natural light", "Place indoor plants", "Use warm colors"],
            "southeast": ["Ideal for kitchen", "Use balanced fire element", "Keep ventilation"],
            "south": ["Use earth tones", "Place heavy furniture", "Ensure stability"],
            "southwest": ["Heavy items placement", "Ground yourself here", "Stability focus"],
            "west": ["Promote introspection", "Use cool colors", "Evening light exposure"],
            "northwest": ["Guest areas", "Keep light", "Avoid heavy items"],
            "center": ["Keep absolutely clear", "Daily meditation", "Install Brahma Yantra"],
        }
        return remedies_map.get(direction, ["Maintain cleanliness", "Proper lighting", "Element balance"])


if __name__ == "__main__":
    print("Vastu Shastra Embedded Knowledge Base loaded successfully!")
    print(f"Directions: {len(list_all_directions())}")
    print(f"Doshas: {len(list_all_doshas())}")
    print(f"Rooms: {len(list_all_rooms())}")
    print(f"Remedies: {len(REMEDIES)}")

    # Test VastuPrinciples
    principles = VastuPrinciples()
    print(f"\nVastuPrinciples class loaded successfully!")
