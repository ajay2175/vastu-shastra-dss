# Vastu KG Expansion - Quick Reference

**Status:** ✅ COMPLETE  
**Date:** 2026-10-08  
**Nodes Expanded:** 138 → 969 (7.0x growth)

---

## Quick Stats

| Metric | Before | After | Growth |
|--------|--------|-------|--------|
| **Nodes** | 138 | 969 | 7.0x |
| **Edges** (Expanded) | 213 | 18,848 | 88.5x |
| **Edges** (Optimized) | 213 | 5,512 | 25.9x |
| **Entity Types** | 13 | 22 | +9 |
| **File Size (Expanded)** | 0.08 MB | 3.96 MB | 50x |
| **File Size (Optimized)** | 0.08 MB | 1.32 MB | 17x |

---

## Two KG Variants

### Expanded KG (Comprehensive)
- **File:** `data/kg/vastu_knowledge_graph_expanded.json`
- **Size:** 3.96 MB
- **Nodes:** 969 | **Edges:** 18,848
- **Use:** Research, learning, complex analysis
- **Best for:** Understanding complete semantic space

### Optimized KG (Production)
- **File:** `data/kg/vastu_knowledge_graph_optimized.json`
- **Size:** 1.32 MB
- **Nodes:** 969 | **Edges:** 5,512
- **Use:** APIs, DSS, real-time queries
- **Best for:** Production deployments (70.8% edge reduction)

---

## Node Distribution (969 total)

```
Top 10 Node Types:
1. direction_room_pair (270)    Direction × Room combinations
2. vastu_dosha (264)            Defects & variations
3. remedy (77)                  Solutions & treatments
4. room (60)                    Space types
5. health_impact (52)           Health outcomes
6. temporal_aspect (49)         Time-based correlations
7. material (27)                Building materials
8. direction (25)               Directional zones
9. color (25)                   Color properties
10. text_source (16)            Information sources

[12 more types with 95 nodes total]
```

---

## Expansion Categories

### Spatial (330 nodes)
- **Directions:** 9 cardinal + 16 sub-directions = 25
- **Rooms:** 60 specific room types
- **Pairs:** 270 direction-room combinations
- **Placements:** Floor-level specifications

### Doshas (264 nodes)
- **Base Defects:** 17 core Vastu doshas
- **Directional:** direction × defect variations
- **Room-Specific:** room × defect variations

### Remedies (77 nodes)
- **Base:** 15 core remedies
- **Material:** 15 material-specific options
- **Color:** 11 color-based remedies
- **Targeted:** 20+ dosha-specific solutions
- **Directional:** 9 direction-based remedies
- **Element:** 5 element-based remedies

### Health & Wellness (52 nodes)
- **Impacts:** 10 primary health outcomes
- **Conditions:** 18 specific health conditions
- **Life Outcomes:** 8 quality-of-life impacts

### Temporal (49 nodes)
- **Daily:** 4 time periods
- **Seasonal:** 5 seasons
- **Muhurtas:** 6 auspicious times
- **Planetary Hours:** 24 day×time combinations
- **Annual Cycles:** 5 yearly events

### Foundations (100+ nodes)
- **Materials:** 27 (stones, metals, composites)
- **Colors:** 25 (base, combinations, properties)
- **Elements:** 14 (base + combinations)
- **Planets:** 18 (navagrahas + associations)
- **Chakras:** 15 (chakras + organs)
- **Sacred Geometry:** 12 (shapes & patterns)
- **Texts:** 16 (classical + modern)
- **Rituals:** 25 (ceremonies, practices)

---

## File Locations (Absolute Paths)

```
Expanded KG:
  /Users/ajaynawale/vastu_shastra_dss/data/kg/vastu_knowledge_graph_expanded.json

Optimized KG:
  /Users/ajaynawale/vastu_shastra_dss/data/kg/vastu_knowledge_graph_optimized.json

Expansion Engine:
  /Users/ajaynawale/vastu_shastra_dss/kg_expansion_engine.py

Optimizer Engine:
  /Users/ajaynawale/vastu_shastra_dss/kg_expansion_optimizer.py

Documentation:
  /Users/ajaynawale/vastu_shastra_dss/KG_EXPANSION_REPORT.md
  /Users/ajaynawale/vastu_shastra_dss/KG_EXPANSION_DELIVERABLES.md
  /Users/ajaynawale/vastu_shastra_dss/KG_EXPANSION_QUICK_REFERENCE.md
```

---

## Deployment

### Option 1: Use Optimized (Recommended for APIs)
```bash
cp data/kg/vastu_knowledge_graph_optimized.json api/kg.json
# Restart API server
```

### Option 2: Use Expanded (Research)
```bash
cp data/kg/vastu_knowledge_graph_expanded.json research/kg.json
```

### Option 3: Both
```bash
ln -s data/kg/vastu_knowledge_graph_optimized.json api/kg.json
ln -s data/kg/vastu_knowledge_graph_expanded.json research/kg.json
```

---

## Key Entity Examples

### Direction-Room Pairs
- `north_master_bedroom` - Optimal bedroom placement
- `northeast_puja_room` - Spiritual room location
- `south_kitchen` - Cooking area direction
- `southeast_fire_element` - Energy placement

### Dosha-Remedy Links
- `blocked_entry` → `remedy_for_blocked_entry`
- `central_pit` → `remedy_for_central_pit`
- `northwest_toilet` → `remedy_for_northwest_toilet`

### Temporal Correlations
- `spring` + `kapha_dosha` → aggravation risk
- `morning` + `fire_element` → optimal energy
- `brahmi_muhurta` → auspicious time for rituals

### Health Chains
- `blocked_entry` → `anxiety` → `insomnia`
- `central_pit` → `financial_loss` → `family_discord`
- `stagnant_water` → `respiratory_problems` → `health_deterioration`

---

## Relation Types (9 in Optimized, 36 in Expanded)

### Most Important (97% of edges)
1. **corrects** (3,960 edges) - Remedy → Dosha
2. **may_have_dosha** (1,350 edges) - Room → Defect
3. **may_aggravate** (150 edges) - Temporal → Health

### Spatial
- `located_in` - Room in Direction
- `placed_in_direction` - Placement specification
- `optimal_in_direction` - Recommended location

### Properties
- `associated_with_element` - Direction → Element
- `ruled_by_planet` - Direction → Planet
- `corresponds_to_chakra` - Direction → Chakra

### Qualitative
- `uses_material` - Remedy → Material
- `represents_element` - Color → Element

---

## Quality Metrics

✅ **All nodes connected** (969/969 = 100%)  
✅ **No orphaned subgraphs**  
✅ **Confidence scores:** 0.75-0.95  
✅ **Bidirectional relations maintained**  
✅ **Duplicate prevention enforced**  
✅ **Schema consistency validated**  

---

## Use Cases Enabled

### Diagnostic Query
```
Input:  West-facing bedroom + blocked entry
Output: 15-20 relevant dosha nodes
        5-10 applicable remedies
        Health impact predictions
```

### Remedy Recommendation
```
Input:  Central pit dosha
Output: 5-10 remedy options
        Material variations
        Placement guidance
        Expected outcomes
```

### Temporal Planning
```
Input:  Current season + time
Output: Aggravated doshas
        Health risks
        Preventive measures
        Optimal activities
```

### Space Optimization
```
Input:  Available room in direction
Output: Optimal room type
        Furniture placement
        Color scheme
        Material recommendations
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Deploy optimized KG to production
2. ✅ Test with 5+ real diagnostic cases
3. ✅ Benchmark query performance
4. ✅ Validate remedy recommendations

### Short Term (Next 2 Weeks)
1. ⏳ Gather user feedback
2. ⏳ Refine confidence scores
3. ⏳ Create specialized sub-KGs
4. ⏳ Document edge cases

### Medium Term (Next Month)
1. ⏳ Extend Ayurvedic correlations
2. ⏳ Add more temporal aspects
3. ⏳ Build visualization tools
4. ⏳ Create mobile app version

---

## Important Notes

⚠️ **Expanded KG (18,848 edges):**
- Comprehensive but dense
- Best for research and learning
- Use for exploratory analysis

⚠️ **Optimized KG (5,512 edges):**
- 70.8% reduction from expanded
- Better query performance
- Recommended for production APIs

⚠️ **Confidence Levels:**
- Original entities: 0.85-0.95
- Derived combinations: 0.75-0.80
- Always use confidence scores for filtering

---

## Quick Commands

```bash
# View expanded KG
python3 -c "import json; kg = json.load(open('data/kg/vastu_knowledge_graph_expanded.json')); 
print(f'Nodes: {len(kg[\"nodes\"])}, Edges: {len(kg[\"edges\"])}')"

# Re-run expansion
python3 kg_expansion_engine.py

# Re-run optimization
python3 kg_expansion_optimizer.py

# Check node types
python3 -c "import json; kg = json.load(open('data/kg/vastu_knowledge_graph_optimized.json')); 
types = {}; [types.update({n['type']: types.get(n['type'],0)+1}) for n in kg['nodes']];
print('\\n'.join(f'{k}: {v}' for k,v in sorted(types.items(), key=lambda x:-x[1])))"
```

---

## Files to Read First

1. **KG_EXPANSION_DELIVERABLES.md** - Comprehensive overview (START HERE)
2. **KG_EXPANSION_REPORT.md** - Detailed analysis and statistics
3. **This file** - Quick reference for fast lookup

---

**Status:** ✅ PRODUCTION READY  
**Last Updated:** 2026-10-08
