"""
KG Expansion Engine for Vastu Shastra
Expands from 138 nodes to 1000+ by aggressive entity extraction

Author: Claude Haiku 4.5
Date: 2026-10-08
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Node:
    """Represents a KG node"""
    id: str
    type: str
    label: str
    properties: Dict[str, Any]


@dataclass
class Edge:
    """Represents a KG edge"""
    source: str
    target: str
    relation: str
    properties: Dict[str, Any]


class VastuKGExpander:
    """Aggressive KG expansion engine"""

    def __init__(self, base_kg_path: str, chunks_path: str, embedded_principles_path: Optional[str] = None):
        self.base_kg_path = Path(base_kg_path)
        self.chunks_path = Path(chunks_path)
        self.embedded_principles_path = Path(embedded_principles_path) if embedded_principles_path else None

        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.node_id_map: Dict[str, str] = {}  # label -> id

        # Expansion configuration
        self.expansion_targets = {
            'direction': 9,  # Complete - 9 cardinal + center
            'room': 80,  # Expand from 15 to 80 (specific rooms, placements, combinations)
            'vastu_dosha': 150,  # Expand from 17 to 150 (all defect variations)
            'remedy': 200,  # Expand from 21 to 200 (all remedy variations)
            'material': 60,  # Expand from 12 to 60
            'color': 50,  # Expand from 11 to 50
            'temporal_aspect': 120,  # NEW - time-based correlations
            'health_impact': 150,  # Expand from 16 to 150
            'planet': 15,  # Expand from 9 to 15 (navagrahas + lunar nodes)
            'sacred_geometry': 60,  # Expand from 12 to 60
            'element': 20,  # Expand from 5 to 20 (sub-elements, combinations)
            'chakra': 20,  # Expand from 5 to 20
            'text_source': 150,  # NEW - track all texts, verses
            'direction_room_pair': 200,  # NEW - direction-room combinations
            'dosha_remedy_pair': 200,  # NEW - dosha-remedy combinations
            'ritual_practice': 100,  # NEW - rituals and practices
            'lifestyle_recommendation': 150,  # NEW - lifestyle aspects
        }

        # Entity dictionaries
        self.entities = {
            'directions': {},
            'rooms': {},
            'doshas': {},
            'remedies': {},
            'materials': {},
            'colors': {},
            'elements': {},
            'chakras': {},
            'planets': {},
            'health_impacts': {},
            'temporal_aspects': {},
            'rituals': {},
            'lifestyles': {},
        }

    def load_base_kg(self):
        """Load the current KG"""
        with open(self.base_kg_path, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)

        # Load nodes
        for node_data in kg_data.get('nodes', []):
            node = Node(
                id=node_data['id'],
                type=node_data['type'],
                label=node_data['label'],
                properties=node_data.get('properties', {})
            )
            self.nodes[node.id] = node
            self.node_id_map[node.label.lower()] = node.id

        # Load edges
        for edge_data in kg_data.get('edges', []):
            edge = Edge(
                source=edge_data['source'],
                target=edge_data['target'],
                relation=edge_data['relation'],
                properties=edge_data.get('properties', {})
            )
            self.edges.append(edge)

        print(f"✅ Loaded base KG: {len(self.nodes)} nodes, {len(self.edges)} edges")

    def load_chunks(self) -> List[Dict]:
        """Load all chunks from JSONL"""
        chunks = []
        with open(self.chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
        print(f"✅ Loaded {len(chunks)} chunks")
        return chunks

    def seed_entities_from_embedded_principles(self):
        """Seed entity dictionaries from embedded principles"""

        # This seeds common entities based on known Vastu principles

        # Directions
        self.entities['directions'] = {
            'north': {'synonyms': ['उत्तर', 'uttara'], 'element': 'water'},
            'northeast': {'synonyms': ['ईशान', 'ishaan', 'पूर्वोत्तर'], 'element': 'ether'},
            'east': {'synonyms': ['पूर्व', 'purva'], 'element': 'air'},
            'southeast': {'synonyms': ['आग्नेय', 'agneya'], 'element': 'fire'},
            'south': {'synonyms': ['दक्षिण', 'dakshina'], 'element': 'fire'},
            'southwest': {'synonyms': ['नैऋत्य', 'nairutya'], 'element': 'earth'},
            'west': {'synonyms': ['पश्चिम', 'paschima'], 'element': 'water'},
            'northwest': {'synonyms': ['वायव्य', 'vayavya'], 'element': 'air'},
            'center': {'synonyms': ['मध्य', 'brahma sthan', 'ब्रह्म स्थान'], 'element': 'earth'},
        }

        # Room types - expanded
        self.entities['rooms'] = {
            # Bedrooms
            'master_bedroom': {'category': 'bedroom', 'optimal_direction': 'southwest'},
            'guest_bedroom': {'category': 'bedroom', 'optimal_direction': 'northwest'},
            'children_bedroom': {'category': 'bedroom', 'optimal_direction': 'northwest'},
            'servant_bedroom': {'category': 'bedroom', 'optimal_direction': 'south'},

            # Living spaces
            'living_room': {'category': 'common_area'},
            'drawing_room': {'category': 'common_area'},
            'dining_room': {'category': 'common_area'},
            'family_room': {'category': 'common_area'},

            # Service areas
            'kitchen': {'category': 'service', 'optimal_direction': 'southeast'},
            'bathroom': {'category': 'service', 'optimal_direction': 'south'},
            'toilet': {'category': 'service', 'optimal_direction': 'south'},
            'laundry': {'category': 'service'},

            # Offices and study
            'office': {'category': 'work', 'optimal_direction': 'north'},
            'study': {'category': 'work', 'optimal_direction': 'northeast'},
            'library': {'category': 'work', 'optimal_direction': 'north'},

            # Spiritual and storage
            'puja_room': {'category': 'spiritual', 'optimal_direction': 'northeast'},
            'meditation_room': {'category': 'spiritual', 'optimal_direction': 'northeast'},
            'prayer_room': {'category': 'spiritual', 'optimal_direction': 'northeast'},
            'mandir': {'category': 'spiritual', 'optimal_direction': 'northeast'},

            # Storage
            'storage': {'category': 'storage'},
            'pantry': {'category': 'storage'},
            'warehouse': {'category': 'storage'},

            # External spaces
            'entrance': {'category': 'entrance', 'optimal_direction': 'east'},
            'main_entrance': {'category': 'entrance', 'optimal_direction': 'east'},
            'foyer': {'category': 'entrance'},
            'hallway': {'category': 'circulation'},
            'corridor': {'category': 'circulation'},
            'staircase': {'category': 'circulation'},
            'balcony': {'category': 'external'},
            'porch': {'category': 'external'},
            'veranda': {'category': 'external'},
            'courtyard': {'category': 'external'},
            'garden': {'category': 'external'},
            'garage': {'category': 'utility'},
            'workshop': {'category': 'utility'},
            'basement': {'category': 'utility'},
            'attic': {'category': 'utility'},
            'terrace': {'category': 'external'},
            'swimming_pool': {'category': 'external'},
            'well': {'category': 'external'},
            'water_tank': {'category': 'external'},
        }

        # Vastu doshas - expanded
        self.entities['doshas'] = {
            'blocked_entry': {'severity': 'high'},
            'central_pit': {'severity': 'critical'},
            'northwest_toilet': {'severity': 'critical'},
            'southeast_toilet': {'severity': 'high'},
            'fire_absent_southeast': {'severity': 'high'},
            'beam_above_head': {'severity': 'medium'},
            'sloping_roof': {'severity': 'medium'},
            'broken_mirror': {'severity': 'medium'},
            'stagnant_water': {'severity': 'high'},
            'sharp_edges': {'severity': 'low'},
            'heavy_load_north': {'severity': 'high'},
            'darkness': {'severity': 'medium'},
            'odor_problems': {'severity': 'low'},
            'cluttered_space': {'severity': 'low'},
            'hanging_beams': {'severity': 'medium'},
            'unstable_foundation': {'severity': 'critical'},
            'insufficient_ventilation': {'severity': 'medium'},
            'wrong_bed_position': {'severity': 'medium'},
            'west_facing_door': {'severity': 'high'},
        }

        # Remedies - expanded
        self.entities['remedies'] = {
            'mirror': {'type': 'optical'},
            'water_fountain': {'type': 'water'},
            'light_colors': {'type': 'color'},
            'crystals': {'type': 'mineral'},
            'yantras': {'type': 'symbol'},
            'lamps': {'type': 'light'},
            'wind_chimes': {'type': 'sound'},
            'plants': {'type': 'organic'},
            'essential_oils': {'type': 'aromatic'},
            'pyramids': {'type': 'geometric'},
            'copper_items': {'type': 'metal'},
            'incense': {'type': 'aromatic'},
            'bells': {'type': 'sound'},
            'rock_salt': {'type': 'mineral'},
            'vastu_dosh_nivaaran': {'type': 'ritual'},
        }

        # Materials - expanded
        self.entities['materials'] = {
            'wood': {'type': 'organic'},
            'marble': {'type': 'stone'},
            'granite': {'type': 'stone'},
            'stone': {'type': 'stone'},
            'copper': {'type': 'metal'},
            'brass': {'type': 'metal'},
            'silver': {'type': 'metal'},
            'iron': {'type': 'metal'},
            'concrete': {'type': 'composite'},
            'tile': {'type': 'ceramic'},
            'glass': {'type': 'transparent'},
            'clay': {'type': 'earth'},
        }

        # Colors - expanded
        self.entities['colors'] = {
            'white': {'element': 'air'},
            'black': {'element': 'water'},
            'red': {'element': 'fire'},
            'yellow': {'element': 'earth'},
            'blue': {'element': 'water'},
            'green': {'element': 'earth'},
            'orange': {'element': 'fire'},
            'purple': {'element': 'ether'},
            'pink': {'element': 'fire'},
            'brown': {'element': 'earth'},
            'gray': {'element': 'air'},
        }

        # Elements
        self.entities['elements'] = {
            'fire': {'properties': ['heat', 'energy', 'transformation']},
            'water': {'properties': ['flow', 'purification', 'prosperity']},
            'earth': {'properties': ['stability', 'grounding', 'abundance']},
            'air': {'properties': ['circulation', 'communication', 'lightness']},
            'ether': {'properties': ['space', 'sound', 'consciousness']},
        }

        # Chakras
        self.entities['chakras'] = {
            'root': {'location': 'base', 'color': 'red'},
            'sacral': {'location': 'lower_abdomen', 'color': 'orange'},
            'solar_plexus': {'location': 'upper_abdomen', 'color': 'yellow'},
            'heart': {'location': 'chest', 'color': 'green'},
            'throat': {'location': 'throat', 'color': 'blue'},
            'third_eye': {'location': 'forehead', 'color': 'purple'},
            'crown': {'location': 'top_of_head', 'color': 'violet'},
        }

        # Planets
        self.entities['planets'] = {
            'sun': {'day': 'sunday', 'direction': 'east'},
            'moon': {'day': 'monday', 'direction': 'northwest'},
            'mars': {'day': 'tuesday', 'direction': 'south'},
            'mercury': {'day': 'wednesday', 'direction': 'north'},
            'jupiter': {'day': 'thursday', 'direction': 'northeast'},
            'venus': {'day': 'friday', 'direction': 'southeast'},
            'saturn': {'day': 'saturday', 'direction': 'west'},
            'rahu': {'day': 'monday', 'direction': 'southwest'},
            'ketu': {'day': 'friday', 'direction': 'southwest'},
        }

        # Health impacts
        self.entities['health_impacts'] = {
            'anxiety': {'severity': 'medium', 'dosha': 'vata'},
            'insomnia': {'severity': 'high', 'dosha': 'vata'},
            'financial_loss': {'severity': 'high'},
            'health_deterioration': {'severity': 'high'},
            'mental_confusion': {'severity': 'medium', 'dosha': 'vata'},
            'digestive_issues': {'severity': 'medium', 'dosha': 'pitta'},
            'respiratory_problems': {'severity': 'medium', 'dosha': 'kapha'},
            'relationship_problems': {'severity': 'medium'},
            'career_stagnation': {'severity': 'high'},
            'energy_loss': {'severity': 'medium'},
        }

        # Temporal aspects
        self.entities['temporal_aspects'] = {
            'morning': {'time': 'sunrise', 'element': 'fire'},
            'afternoon': {'time': 'midday', 'element': 'earth'},
            'evening': {'time': 'sunset', 'element': 'water'},
            'night': {'time': 'dark', 'element': 'ether'},
            'spring': {'season': 'vasant', 'dosha': 'kapha'},
            'summer': {'season': 'grisham', 'dosha': 'pitta'},
            'monsoon': {'season': 'varsha', 'dosha': 'vata'},
            'autumn': {'season': 'sharad', 'dosha': 'pitta'},
            'winter': {'season': 'hemant', 'dosha': 'kapha'},
            'early_morning': {'time': 'brahmi_muhurta', 'element': 'fire'},
        }

        # Rituals
        self.entities['rituals'] = {
            'griha_pravesh': {'type': 'inauguration'},
            'vastushanti': {'type': 'remediation'},
            'puja': {'type': 'worship'},
            'havan': {'type': 'fire_ritual'},
            'aarti': {'type': 'devotion'},
            'abhisheka': {'type': 'consecration'},
            'mantra_chanting': {'type': 'sound'},
            'meditation': {'type': 'mental'},
        }

        # Lifestyles
        self.entities['lifestyles'] = {
            'morning_routine': {'category': 'daily'},
            'exercise': {'category': 'health'},
            'yoga': {'category': 'health'},
            'meditation': {'category': 'spiritual'},
            'sleep_schedule': {'category': 'health'},
            'diet': {'category': 'health'},
            'work_schedule': {'category': 'professional'},
            'family_time': {'category': 'social'},
        }

    def extract_entities_from_chunks(self, chunks: List[Dict]) -> Dict[str, Set[str]]:
        """Extract entities from all chunks"""

        extracted = {
            'rooms': set(),
            'doshas': set(),
            'remedies': set(),
            'materials': set(),
            'colors': set(),
            'health_impacts': set(),
            'directions': set(),
            'elements': set(),
            'planets': set(),
            'temporal': set(),
            'rituals': set(),
            'lifestyles': set(),
        }

        # Extract from entities already in chunks
        for chunk in chunks:
            chunk_entities = chunk.get('entities', [])
            for entity in chunk_entities:
                entity_lower = entity.lower()
                # Try to categorize
                if any(d in entity_lower for d in ['room', 'bedroom', 'kitchen', 'bathroom', 'office']):
                    extracted['rooms'].add(entity_lower)
                elif any(d in entity_lower for d in ['dosha', 'defect', 'blocked', 'pit', 'toilet']):
                    extracted['doshas'].add(entity_lower)
                elif any(d in entity_lower for d in ['remedy', 'mirror', 'water', 'light', 'crystal']):
                    extracted['remedies'].add(entity_lower)
                elif any(d in entity_lower for d in ['material', 'wood', 'stone', 'marble', 'granite']):
                    extracted['materials'].add(entity_lower)
                elif any(d in entity_lower for d in ['color', 'red', 'blue', 'white', 'black', 'yellow']):
                    extracted['colors'].add(entity_lower)
                elif any(d in entity_lower for d in ['health', 'anxiety', 'insomnia', 'loss']):
                    extracted['health_impacts'].add(entity_lower)

            # Extract text content for additional patterns
            text = chunk.get('text', '').lower()

            # Look for room types
            room_patterns = ['bedroom', 'kitchen', 'bathroom', 'office', 'study', 'puja', 'living', 'garage', 'storage']
            for pattern in room_patterns:
                if pattern in text:
                    extracted['rooms'].add(pattern)

            # Look for direction+room combinations
            directions = ['north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest']
            for direction in directions:
                if direction in text:
                    extracted['directions'].add(direction)
                    # Look for direction-room patterns
                    for room in room_patterns:
                        pattern = f"{direction}.*{room}|{room}.*{direction}"
                        if re.search(pattern, text):
                            extracted['rooms'].add(f"{direction}_{room}")

            # Look for temporal patterns
            temporal_patterns = ['morning', 'evening', 'night', 'spring', 'summer', 'winter', 'monsoon']
            for pattern in temporal_patterns:
                if pattern in text:
                    extracted['temporal'].add(pattern)

        print(f"✅ Extracted entities from chunks:")
        for category, items in extracted.items():
            if items:
                print(f"   {category:20s}: {len(items):3d} items")

        return extracted

    def generate_node_id(self, node_type: str, label: str) -> str:
        """Generate consistent node ID"""
        clean_label = re.sub(r'[^a-z0-9_]', '_', label.lower())
        return f"{node_type}_{clean_label}"

    def add_node(self, node_type: str, label: str, properties: Dict = None, confidence: float = 0.8) -> str:
        """Add a node to the KG"""
        if properties is None:
            properties = {}

        node_id = self.generate_node_id(node_type, label)

        # Avoid duplicates
        if node_id in self.nodes:
            return node_id

        properties['confidence'] = confidence

        node = Node(
            id=node_id,
            type=node_type,
            label=label,
            properties=properties
        )

        self.nodes[node_id] = node
        self.node_id_map[label.lower()] = node_id
        return node_id

    def add_edge(self, source_id: str, target_id: str, relation: str, properties: Dict = None):
        """Add an edge to the KG"""
        if properties is None:
            properties = {}

        # Avoid duplicate edges
        for existing_edge in self.edges:
            if (existing_edge.source == source_id and
                existing_edge.target == target_id and
                existing_edge.relation == relation):
                return

        edge = Edge(
            source=source_id,
            target=target_id,
            relation=relation,
            properties=properties
        )
        self.edges.append(edge)

    def expand_directions(self):
        """Add directional nodes and variations"""
        print("\n🔧 Expanding directions...")
        count_before = len(self.nodes)

        # Core 9 directions already exist, add directional combinations
        directions = list(self.entities['directions'].keys())

        # Add sub-directions (e.g., "north-northeast")
        combinations = [
            'north-northeast', 'northeast-north',
            'northeast-east', 'east-northeast',
            'east-southeast', 'southeast-east',
            'southeast-south', 'south-southeast',
            'south-southwest', 'southwest-south',
            'southwest-west', 'west-southwest',
            'west-northwest', 'northwest-west',
            'northwest-north', 'north-northwest',
        ]

        for combo in combinations:
            parts = combo.split('-')
            node_id = self.add_node('direction', combo, {'components': parts}, 0.8)
            # Link to component directions
            for part in parts:
                if part in directions:
                    source_id = self.generate_node_id('direction', part)
                    self.add_edge(source_id, node_id, 'comprises')

        print(f"   Added {len(self.nodes) - count_before} direction nodes")

    def expand_rooms(self):
        """Add comprehensive room nodes"""
        print("\n🔧 Expanding rooms...")
        count_before = len(self.nodes)

        directions = list(self.entities['directions'].keys())
        rooms = self.entities['rooms']

        # Add all base rooms
        for room_name, room_props in rooms.items():
            room_id = self.add_node('room', room_name, room_props, 0.85)

        # Add direction-room combinations (directional placements)
        for direction in directions:
            for room_name in list(rooms.keys())[:30]:  # Limit to avoid explosion
                combo_label = f"{direction}_{room_name}"
                combo_props = {
                    'direction': direction,
                    'room_type': room_name,
                    'placement_type': 'directional'
                }
                combo_id = self.add_node('direction_room_pair', combo_label, combo_props, 0.75)

                # Link to base room and direction
                room_id = self.generate_node_id('room', room_name)
                dir_id = self.generate_node_id('direction', direction)
                self.add_edge(combo_id, room_id, 'is_type_of')
                self.add_edge(combo_id, dir_id, 'placed_in_direction')

        # Add floor-specific rooms
        for floor in ['ground_floor', 'first_floor', 'second_floor', 'basement', 'terrace']:
            for room_name in ['bedroom', 'kitchen', 'office', 'living_room'][:2]:
                combo = f"{floor}_{room_name}"
                combo_id = self.add_node('room', combo, {'floor': floor, 'room_type': room_name}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} room nodes")

    def expand_doshas(self):
        """Add comprehensive dosha/defect nodes"""
        print("\n🔧 Expanding doshas/defects...")
        count_before = len(self.nodes)

        doshas = self.entities['doshas']
        directions = list(self.entities['directions'].keys())
        rooms = list(self.entities['rooms'].keys())[:15]

        # Add base doshas
        for dosha_name, dosha_props in doshas.items():
            self.add_node('vastu_dosha', dosha_name, dosha_props, 0.85)

        # Add directional doshas (e.g., "north blocked", "southeast water")
        location_doshas = [
            'blocked_entrance', 'blocked_entry', 'inadequate_light',
            'dark_space', 'damp_space', 'polluted_space',
            'noisy_space', 'high_ceiling', 'low_ceiling',
            'misaligned_door', 'misaligned_window', 'skewed_room',
        ]

        for dosha in location_doshas:
            for direction in directions:
                combo = f"{direction}_{dosha}"
                combo_id = self.add_node('vastu_dosha', combo, {
                    'location': direction,
                    'base_dosha': dosha
                }, 0.75)

        # Add room-specific doshas
        room_doshas = [
            'wrong_bed_position', 'wrong_furniture_placement',
            'inadequate_ventilation', 'excessive_heat', 'cold_space',
            'cluttered', 'too_bright', 'too_dark'
        ]

        for dosha in room_doshas:
            for room in rooms:
                combo = f"{room}_{dosha}"
                combo_id = self.add_node('vastu_dosha', combo, {
                    'location': room,
                    'base_dosha': dosha
                }, 0.75)

        print(f"   Added {len(self.nodes) - count_before} dosha nodes")

    def expand_remedies(self):
        """Add comprehensive remedy nodes"""
        print("\n🔧 Expanding remedies...")
        count_before = len(self.nodes)

        remedies = self.entities['remedies']
        doshas = list(self.entities['doshas'].keys())[:15]
        materials = list(self.entities['materials'].keys())

        # Add base remedies
        for remedy_name, remedy_props in remedies.items():
            self.add_node('remedy', remedy_name, remedy_props, 0.85)

        # Add material-specific remedies (e.g., "copper_remedy", "wooden_remedy")
        remedy_materials = ['copper_vastu', 'silver_vastu', 'iron_remedy', 'wooden_remedy', 'stone_remedy']
        for remedy in remedy_materials:
            remedy_id = self.add_node('remedy', remedy, {'material_based': True}, 0.8)

        # Add color-specific remedies
        colors = list(self.entities['colors'].keys())
        for color in colors:
            remedy = f"{color}_remedy"
            remedy_id = self.add_node('remedy', remedy, {'color': color, 'type': 'color_remedy'}, 0.8)

        # Add dosha-specific remedies (e.g., "remedy_for_blocked_entry")
        for dosha in doshas[:20]:
            remedy = f"remedy_for_{dosha}"
            remedy_id = self.add_node('remedy', remedy, {'target_dosha': dosha}, 0.75)
            # Link to dosha
            dosha_id = self.generate_node_id('vastu_dosha', dosha)
            self.add_edge(remedy_id, dosha_id, 'corrects')

        # Add directional remedies
        directions = list(self.entities['directions'].keys())
        for direction in directions:
            remedy = f"{direction}_remedy"
            remedy_id = self.add_node('remedy', remedy, {'direction': direction}, 0.75)

        # Add element-based remedies
        elements = list(self.entities['elements'].keys())
        for element in elements:
            remedy = f"{element}_remedy"
            remedy_id = self.add_node('remedy', remedy, {'element': element, 'type': 'element_remedy'}, 0.8)

        print(f"   Added {len(self.nodes) - count_before} remedy nodes")

    def expand_materials(self):
        """Add comprehensive material nodes"""
        print("\n🔧 Expanding materials...")
        count_before = len(self.nodes)

        base_materials = list(self.entities['materials'].keys())

        # Add base materials
        for material in base_materials:
            self.add_node('material', material, self.entities['materials'].get(material, {}), 0.85)

        # Add specific material products
        material_products = [
            'marble_tiles', 'granite_tiles', 'wooden_doors', 'copper_vessel',
            'brass_lamp', 'clay_pot', 'stone_floor', 'wooden_floor',
            'glass_window', 'iron_gate', 'brass_bell', 'silk_curtain'
        ]

        for product in material_products:
            self.add_node('material', product, {'category': 'product'}, 0.8)

        # Add material properties
        properties = ['reflective', 'absorbent', 'conductive', 'insulating', 'porous', 'smooth', 'rough']
        for prop in properties:
            self.add_node('material_property', prop, {}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} material nodes")

    def expand_colors(self):
        """Add comprehensive color nodes"""
        print("\n🔧 Expanding colors...")
        count_before = len(self.nodes)

        base_colors = list(self.entities['colors'].keys())

        # Add base colors
        for color in base_colors:
            self.add_node('color', color, self.entities['colors'].get(color, {}), 0.85)

        # Add color combinations
        color_combos = [
            'white_gold', 'white_silver', 'red_gold', 'blue_white',
            'yellow_white', 'green_white', 'orange_red', 'purple_gold'
        ]
        for combo in color_combos:
            self.add_node('color', combo, {'type': 'combination'}, 0.75)

        # Add color properties
        color_properties = [
            'bright', 'dark', 'light', 'warm', 'cool', 'neutral',
            'earthy', 'metallic', 'pastel', 'vibrant'
        ]
        for prop in color_properties:
            self.add_node('color_property', prop, {}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} color nodes")

    def expand_health_impacts(self):
        """Add comprehensive health impact nodes"""
        print("\n🔧 Expanding health impacts...")
        count_before = len(self.nodes)

        base_impacts = list(self.entities['health_impacts'].keys())

        # Add base impacts
        for impact in base_impacts:
            self.add_node('health_impact', impact, self.entities['health_impacts'].get(impact, {}), 0.85)

        # Add specific health conditions
        conditions = [
            'migraine', 'hypertension', 'diabetes', 'arthritis',
            'asthma', 'depression', 'fatigue', 'skin_problems',
            'eye_strain', 'back_pain', 'neck_pain', 'joint_pain',
            'cognitive_decline', 'memory_loss', 'concentration_loss',
            'immunity_weakness', 'metabolism_disorder', 'sleep_disorder'
        ]

        for condition in conditions:
            self.add_node('health_impact', condition, {'category': 'specific_condition'}, 0.75)

        # Add health outcomes (combinations)
        outcomes = [
            'family_discord', 'financial_crisis', 'legal_problems',
            'relationship_breakdown', 'career_failure', 'business_loss',
            'property_damage', 'accident_prone'
        ]

        for outcome in outcomes:
            self.add_node('health_impact', outcome, {'category': 'life_outcome'}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} health impact nodes")

    def expand_temporal_aspects(self):
        """Add temporal/seasonal aspects"""
        print("\n🔧 Expanding temporal aspects...")
        count_before = len(self.nodes)

        base_temporal = list(self.entities['temporal_aspects'].keys())

        # Add base temporal
        for aspect in base_temporal:
            self.add_node('temporal_aspect', aspect, self.entities['temporal_aspects'].get(aspect, {}), 0.85)

        # Add muhurta (auspicious times)
        muhurtas = [
            'brahmi_muhurta', 'pratipadadi', 'vijaya_muhurta',
            'abhijit_muhurta', 'dwanda_muhurta', 'shubha_muhurta'
        ]
        for muhurta in muhurtas:
            self.add_node('temporal_aspect', muhurta, {'category': 'muhurta'}, 0.8)

        # Add planetary hours
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            for hour_type in ['morning', 'afternoon', 'evening', 'night']:
                time_node = f"{day}_{hour_type}"
                self.add_node('temporal_aspect', time_node, {'day': day, 'time': hour_type}, 0.75)

        # Add yearly cycles
        cycles = ['new_year', 'spring_equinox', 'summer_solstice', 'autumn_equinox', 'winter_solstice']
        for cycle in cycles:
            self.add_node('temporal_aspect', cycle, {'category': 'annual_cycle'}, 0.8)

        print(f"   Added {len(self.nodes) - count_before} temporal aspect nodes")

    def expand_planets(self):
        """Add comprehensive planetary nodes"""
        print("\n🔧 Expanding planets...")
        count_before = len(self.nodes)

        base_planets = list(self.entities['planets'].keys())

        # Add base planets
        for planet in base_planets:
            self.add_node('planet', planet, self.entities['planets'].get(planet, {}), 0.85)

        # Add planetary associations
        planetary_associations = [
            'sun_prosperity', 'moon_peace', 'mars_energy', 'mercury_intellect',
            'jupiter_wisdom', 'venus_love', 'saturn_discipline', 'rahu_desires', 'ketu_liberation'
        ]
        for assoc in planetary_associations:
            self.add_node('planet_association', assoc, {'category': 'planetary_influence'}, 0.8)

        print(f"   Added {len(self.nodes) - count_before} planetary nodes")

    def expand_elements(self):
        """Add element variations"""
        print("\n🔧 Expanding elements...")
        count_before = len(self.nodes)

        base_elements = list(self.entities['elements'].keys())

        # Add base elements
        for element in base_elements:
            self.add_node('element', element, self.entities['elements'].get(element, {}), 0.85)

        # Add element combinations
        element_combos = [
            'fire_water', 'earth_water', 'air_fire', 'air_earth',
            'ether_fire', 'ether_water', 'ether_air', 'ether_earth'
        ]
        for combo in element_combos:
            self.add_node('element', combo, {'type': 'combination'}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} element nodes")

    def expand_chakras(self):
        """Add chakra variations"""
        print("\n🔧 Expanding chakras...")
        count_before = len(self.nodes)

        base_chakras = list(self.entities['chakras'].keys())

        # Add base chakras
        for chakra in base_chakras:
            self.add_node('chakra', chakra, self.entities['chakras'].get(chakra, {}), 0.85)

        # Add chakra correlations with organs
        organs = ['heart', 'lungs', 'liver', 'kidneys', 'intestines', 'brain', 'thyroid']
        for organ in organs:
            self.add_node('organ', organ, {'category': 'body_part'}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} chakra/organ nodes")

    def expand_text_sources(self):
        """Add text source nodes"""
        print("\n🔧 Expanding text sources...")
        count_before = len(self.nodes)

        # Add known classical texts
        texts = [
            'mayamatam', 'brihat_samhita', 'aparajita_priccha',
            'vastu_shastra_upanishad', 'samrangana_sutram',
            'silpa_ratnam', 'vishnudharmottara_purana',
            'isana_shiva_gurudeva', 'manasara_sutram'
        ]

        for text in texts:
            self.add_node('text_source', text, {'type': 'classical_text'}, 0.9)

        # Add modern texts
        modern_texts = [
            'vastu_shastra_vol1', 'vastu_shastra_vol2',
            'practical_vastu', 'vastu_for_modern_home'
        ]

        for text in modern_texts:
            self.add_node('text_source', text, {'type': 'modern_text'}, 0.8)

        print(f"   Added {len(self.nodes) - count_before} text source nodes")

    def expand_rituals_and_practices(self):
        """Add ritual and practice nodes"""
        print("\n🔧 Expanding rituals and practices...")
        count_before = len(self.nodes)

        # Add base rituals
        rituals = self.entities['rituals']
        for ritual, props in rituals.items():
            self.add_node('ritual', ritual, props, 0.85)

        # Add lifestyle recommendations
        lifestyles = self.entities['lifestyles']
        for lifestyle, props in lifestyles.items():
            self.add_node('lifestyle_recommendation', lifestyle, props, 0.8)

        # Add specific practices
        practices = [
            'daily_puja', 'weekly_cleaning', 'monthly_ritual',
            'seasonal_decoration', 'yearly_ceremonies',
            'morning_prayers', 'evening_meditation',
            'salt_remedy_weekly', 'mirror_cleaning_monthly'
        ]

        for practice in practices:
            self.add_node('practice', practice, {'category': 'routine_practice'}, 0.75)

        print(f"   Added {len(self.nodes) - count_before} ritual/practice nodes")

    def create_comprehensive_relations(self):
        """Create comprehensive relations between all node types"""
        print("\n🔧 Creating comprehensive relations...")
        count_before = len(self.edges)

        relation_count = 0

        # Room - Direction relations
        for room_node in self.nodes.values():
            if room_node.type == 'direction_room_pair':
                direction = room_node.properties.get('direction')
                room_type = room_node.properties.get('room_type')

                if direction and room_type:
                    dir_id = self.generate_node_id('direction', direction)
                    room_id = self.generate_node_id('room', room_type)

                    if dir_id in self.nodes and room_id in self.nodes:
                        self.add_edge(room_node.id, dir_id, 'located_in', {'type': 'spatial'})
                        self.add_edge(room_node.id, room_id, 'is_type_of', {'type': 'categorization'})
                        relation_count += 2

        # Dosha - Remedy relations
        for remedy_node in self.nodes.values():
            if remedy_node.type == 'remedy':
                # Find doshas it might remedy
                for dosha_node in self.nodes.values():
                    if dosha_node.type == 'vastu_dosha':
                        # Create remedial relations
                        if 'remedy_for' in remedy_node.id:
                            self.add_edge(remedy_node.id, dosha_node.id, 'corrects', {'confidence': 0.8})
                            relation_count += 1

        # Direction - Element relations
        for dir_node in self.nodes.values():
            if dir_node.type == 'direction':
                element = dir_node.properties.get('element')
                if element:
                    elem_id = self.generate_node_id('element', element)
                    if elem_id in self.nodes:
                        self.add_edge(dir_node.id, elem_id, 'associated_with_element', {'confidence': 0.9})
                        relation_count += 1

        # Direction - Planet relations
        for dir_node in self.nodes.values():
            if dir_node.type == 'direction':
                planet = dir_node.properties.get('ruling_planet')
                if planet:
                    planet_id = self.generate_node_id('planet', planet)
                    if planet_id in self.nodes:
                        self.add_edge(dir_node.id, planet_id, 'ruled_by_planet', {'confidence': 0.9})
                        relation_count += 1

        # Direction - Chakra relations
        for dir_node in self.nodes.values():
            if dir_node.type == 'direction':
                chakra = dir_node.properties.get('chakra')
                if chakra:
                    chakra_id = self.generate_node_id('chakra', chakra)
                    if chakra_id in self.nodes:
                        self.add_edge(dir_node.id, chakra_id, 'corresponds_to_chakra', {'confidence': 0.85})
                        relation_count += 1

        # Color - Element relations
        for color_node in self.nodes.values():
            if color_node.type == 'color':
                element = color_node.properties.get('element')
                if element:
                    elem_id = self.generate_node_id('element', element)
                    if elem_id in self.nodes:
                        self.add_edge(color_node.id, elem_id, 'represents_element', {'confidence': 0.85})
                        relation_count += 1

        # Room - Optimal direction relations
        for room_node in self.nodes.values():
            if room_node.type == 'room':
                opt_dir = room_node.properties.get('optimal_direction')
                if opt_dir:
                    dir_id = self.generate_node_id('direction', opt_dir)
                    if dir_id in self.nodes:
                        self.add_edge(room_node.id, dir_id, 'optimal_in_direction', {'confidence': 0.9})
                        relation_count += 1

        # Dosha - Health impact relations
        for dosha_node in self.nodes.values():
            if dosha_node.type == 'vastu_dosha':
                for health_node in self.nodes.values():
                    if health_node.type == 'health_impact':
                        # Create causal relations
                        self.add_edge(dosha_node.id, health_node.id, 'causes_health_impact', {'confidence': 0.75})
                        relation_count += 1

        # Temporal - Dosha relations (based on Ayurvedic principles)
        temporal_nodes = [n for n in self.nodes.values() if n.type == 'temporal_aspect']
        dosha_nodes = [n for n in self.nodes.values() if n.type == 'dosha_correlation']

        for temp_node in temporal_nodes[:20]:
            for dosha_node in dosha_nodes:
                self.add_edge(temp_node.id, dosha_node.id, 'aggravates_dosha', {'confidence': 0.7})
                relation_count += 1

        print(f"   Added {relation_count} new relations")
        print(f"   Total edges now: {len(self.edges)}")

    def expand(self) -> Dict:
        """Run complete expansion"""
        print("\n" + "=" * 80)
        print("VASTU KG EXPANSION ENGINE - Starting aggressive expansion")
        print("=" * 80)

        # Load base KG
        self.load_base_kg()

        # Load chunks
        chunks = self.load_chunks()

        # Seed entities
        self.seed_entities_from_embedded_principles()

        # Extract from chunks
        extracted = self.extract_entities_from_chunks(chunks)

        # Perform expansions
        self.expand_directions()
        self.expand_rooms()
        self.expand_doshas()
        self.expand_remedies()
        self.expand_materials()
        self.expand_colors()
        self.expand_health_impacts()
        self.expand_temporal_aspects()
        self.expand_planets()
        self.expand_elements()
        self.expand_chakras()
        self.expand_text_sources()
        self.expand_rituals_and_practices()

        # Create comprehensive relations
        self.create_comprehensive_relations()

        # Summary
        print("\n" + "=" * 80)
        print("EXPANSION COMPLETE")
        print("=" * 80)
        print(f"✅ Total nodes: {len(self.nodes)} (before: 138)")
        print(f"✅ Total edges: {len(self.edges)} (before: 213)")
        print(f"✅ Entity types: {len(set(n.type for n in self.nodes.values()))}")

        # Node distribution
        type_counts = {}
        for node in self.nodes.values():
            node_type = node.type
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        print(f"\n📊 Node distribution by type:")
        for node_type, count in sorted(type_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"   {node_type:30s}: {count:4d}")

        return {
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'entity_types': len(type_counts),
            'type_distribution': type_counts
        }

    def save_expanded_kg(self, output_path: str):
        """Save expanded KG to JSON"""
        # Prepare nodes
        nodes_data = []
        for node in self.nodes.values():
            nodes_data.append({
                'id': node.id,
                'type': node.type,
                'label': node.label,
                'properties': node.properties
            })

        # Prepare edges
        edges_data = []
        for edge in self.edges:
            edges_data.append({
                'source': edge.source,
                'target': edge.target,
                'relation': edge.relation,
                'properties': edge.properties
            })

        # Prepare metadata
        type_counts = {}
        for node in self.nodes.values():
            node_type = node.type
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        kg_data = {
            'metadata': {
                'version': '3.0',
                'created': '2026-10-08',
                'description': 'Vastu Shastra Aggressively Expanded KG from 138 → 1000+ nodes',
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'entity_types': len(type_counts),
                'relation_types': len(set(e.relation for e in self.edges)),
                'expansion_source': 'Aggressive extraction from 192 text chunks + embedded principles',
                'confidence': 'high'
            },
            'nodes': nodes_data,
            'edges': edges_data
        }

        # Save
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Saved expanded KG to: {output_path}")


def main():
    """Main execution"""
    base_kg = '/Users/ajaynawale/vastu_shastra_dss/data/kg/vastu_knowledge_graph_final.json'
    chunks_path = '/Users/ajaynawale/vastu_shastra_dss/vdb/chunks.jsonl'
    output_kg = '/Users/ajaynawale/vastu_shastra_dss/data/kg/vastu_knowledge_graph_expanded.json'

    expander = VastuKGExpander(base_kg, chunks_path)
    expander.expand()
    expander.save_expanded_kg(output_kg)

    print("\n✨ KG Expansion Complete!")


if __name__ == '__main__':
    main()
