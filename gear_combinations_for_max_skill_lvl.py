"""
Gear Optimizer (WITH INTELLIGENT SUGGESTIONS)
============================================
- Finds closest combinations if perfect is impossible
- Shows ALL equally best results
- Suggests improvements (what to swap)
"""

from itertools import combinations, product

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
GLOBAL_ALL_SKILLS = 1 # from talisman

SKILL_TARGETS = {
    "healing": 12,
    "soul amulet": 12,
    "poisoning": 12,
    "summoning": 13,
    "qi of infinity": 12,
}

ALL_SKILLS = list(SKILL_TARGETS.keys())

SLOT_LIMITS = {
    "helmet": 1,
    "armour": 1,
    "bracer": 2,
    "ring": 2,
    "boots": 1,
    "belt": 1,
}

GEAR = [
    {"id": 1, "slot": "helmet", "skills": {"summoning": 1, "healing": 1}},
    {"id": 2, "slot": "armour", "skills": {"soul amulet": 1, "qi of infinity": 1}},
    {"id": 3, "slot": "bracer", "skills": {"summoning": 1, "qi of infinity": 1}},
    {"id": 4, "slot": "belt", "skills": {"healing": 1, "poisoning": 1}},
    {"id": 5, "slot": "ring", "skills": {"qi of infinity": 1, "poisoning": 1}},
    {"id": 6, "slot": "boots", "skills": {"summoning": 1, "soul amulet": 1}},
    {"id": 7, "slot": "bracer", "skills": {"qi of infinity": 1, "soul amulet": 1}},
    {"id": 8, "slot": "ring", "skills": {"healing": 1, "summoning": 1}},
    # {"id": 9, "slot": "ring", "skills": {"poisoning": 1, "soul amulet": 1}},
    # {"id": 10, "slot": "ring", "skills": {"qi of infinity": 1, "healing": 1}},
    {"id": 11, "slot": "bracer", "skills": {"poisoning": 1, "healing": 1}},
    {"id": 12, "slot": "helmet", "skills": {"poisoning": 1, "soul amulet": 1}},
    {"id": 13, "slot": "helmet", "skills": {"summoning": 1, "soul amulet": 1}},
    {"id": 14, "slot": "helmet", "skills": {"summoning": 1, "qi of infinity": 1}},
]

GEAR_NAMES = {
    1: "Helmet      — all, summoning, healing",
    2: "Armour      — all, soul amulet, qi",
    3: "Bracer A    — all, summoning, qi",
    4: "Belt        — all, healing, poisoning",
    5: "Ring A      — all, qi, poisoning",
    6: "Boots       — all, summoning, soul amulet",
    7: "Bracer B    — all, qi, soul amulet",
    8: "Ring B      — all, healing, summoning",
    # 9: "Ring C      — all, poisoning, soul amulet",
    # 10: "Ring D      — all, qi, healing",
    11: "Bracer C    — all, poisoning, healing",
    12: "Helmet B     — all, poisoning, soul amulet",
    13: "Helmet C     — all, summoning, soul amulet",
    14: "Helmet D     — all, summoning, qi of infinity",
}

# ─────────────────────────────────────────────
# CORE
# ─────────────────────────────────────────────

def compute_skills(loadout):
    totals = {s: GLOBAL_ALL_SKILLS for s in ALL_SKILLS}

    for piece in loadout:
        for skill in ALL_SKILLS:
            totals[skill] += 1

        for skill, bonus in piece["skills"].items():
            totals[skill] += bonus

    return totals


def evaluate(loadout):
    totals = compute_skills(loadout)

    deficit = 0
    overshoot = 0
    diff_map = {}

    for skill, target in SKILL_TARGETS.items():
        diff = totals[skill] - target
        diff_map[skill] = diff

        if diff < 0:
            deficit += abs(diff)
        else:
            overshoot += diff

    return deficit, overshoot, totals, diff_map


def generate_loadouts():
    by_slot = {
        slot: [g for g in GEAR if g["slot"] == slot]
        for slot in SLOT_LIMITS
    }

    slot_options = {
        slot: list(combinations(pieces, SLOT_LIMITS[slot]))
        for slot, pieces in by_slot.items()
    }

    for combo in product(*slot_options.values()):
        loadout = []
        for part in combo:
            loadout.extend(part)
        yield loadout


# ─────────────────────────────────────────────
# SUGGESTION ENGINE 🔥
# ─────────────────────────────────────────────

def suggest_improvements(loadout, diff_map):
    missing = [s for s, d in diff_map.items() if d < 0]
    excess = [s for s, d in diff_map.items() if d > 0]

    suggestions = []

    for piece in loadout:
        piece_skills = piece["skills"]

        gives_excess = any(s in piece_skills for s in excess)

        if not gives_excess:
            continue

        for alt in GEAR:
            if alt["slot"] != piece["slot"] or alt["id"] == piece["id"]:
                continue

            alt_skills = alt["skills"]

            helps_missing = any(s in alt_skills for s in missing)

            if helps_missing:
                suggestions.append(
                    f"Replace [{piece['slot']}] {GEAR_NAMES[piece['id']]} "
                    f"→ {GEAR_NAMES[alt['id']]}"
                )

    return list(set(suggestions))



# Define these at the top of your file (global scope)
total_slot_counts = {}
total_slot_skills = {}

total_all_solutions = []

def suggest_per_combination(loadout, diff_map):
    global total_slot_counts, total_all_solutions
    
    print("\nFix options:")

    # Get missing skills (deficit) and overshoot skills
    missing = {s: d for s, d in diff_map.items() if d < 0}
    overshoot = {s: d for s, d in diff_map.items() if d > 0}

    if not missing:
        print("  Already optimal")
        return

    # Total deficit
    total_deficit = sum(abs(d) for d in missing.values())
    
    # Get all skills
    all_skills = list(diff_map.keys())


    slot_counts = {}
    all_solutions = []

    # ─────────────────────────────
    # CASE 1: ONE ITEM CAN FIX IT
    # ─────────────────────────────
    if total_deficit <= 2:
        print("  ✅ Can be fixed with ONE new item:\n")

        # For each missing skill, we need +1 or +2
        for missing_skill, deficit in missing.items():
            needed = abs(deficit)  # How many points we need (1 or 2)
            
            # Look for items that have overshoot skills to replace
            for piece in loadout:
                # Get current item's skills from the piece
                current_skills = piece.get('skills', [])
                
                # Check if this piece has any overshoot skills
                has_overshoot = any(skill in overshoot for skill in current_skills if skill != 'all')
                
                if has_overshoot or True:  # Even if no overshoot, we can still replace
                    # Try replacing with an item that has the missing skill
                    for i, s1 in enumerate(all_skills):
                        for s2 in all_skills[i+1:]:
                            # Check if this combination provides the missing skill
                            if missing_skill not in (s1, s2):
                                continue
                            
                            # Simulate the replacement
                            new_diff = diff_map.copy()
                            
                            # Remove current item's skills
                            for skill in current_skills:
                                if skill == 'all':
                                    for s in all_skills:
                                        new_diff[s] -= 1
                                else:
                                    new_diff[skill] -= 1
                            
                            # Add new item's skills
                            new_diff[s1] += 1
                            new_diff[s2] += 1
                            
                            # Check if all skills are >= 0
                            if all(v >= 0 for v in new_diff.values()):
                                gear_name = piece.get('name', f"Item {piece['id']}")
                                solution = {
                                    'piece': piece,
                                    'slot': piece['slot'],
                                    'gear_name': gear_name,
                                    'skills': (s1, s2),
                                    'fixes_target': new_diff[missing_skill] >= 0
                                }
                                all_solutions.append(solution)
                                
                                # Count by slot type across ALL combinations
                                slot = piece['slot']
                                slot_counts[slot] = slot_counts.get(slot, 0) + 1
                                total_slot_counts[slot] = total_slot_counts.get(slot, 0) + 1
                                skill_pair = tuple(sorted((s1, s2)))
                                if slot not in total_slot_skills:
                                    total_slot_skills[slot] = {}
                                total_slot_skills[slot][skill_pair] = total_slot_skills[slot].get(skill_pair, 0) + 1
                                
        
        # Show solutions for THIS combination
        if all_solutions:
            # Sort solutions: prioritize ones that fix the target, then by slot
            all_solutions.sort(key=lambda x: (not x['fixes_target'], x['slot']))
            total_all_solutions.append(all_solutions)
            
            print("  Replaceable gear pieces:")
            for sol in all_solutions:
                s1, s2 = sol['skills']
                print(f"    • [{sol['slot']:8}] {sol['gear_name']} → ({s1} + {s2})")
            
            # Show slot frequency
            print("\n  📊 Slot replacement frequency:")
            for slot, count in sorted(slot_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    • {slot}: {count} possible replacement(s)")

        print("  (Any slot can be replaced with correct stats)\n")
        return

    # ─────────────────────────────
    # CASE 2: NEED MULTIPLE ITEMS
    # ─────────────────────────────

    print(f"  ❌ Needs at least {(total_deficit + 1)//2} new items\n")
    print("  Best item stats to look for:")

    shown = set()
    
    # Prioritize fixing missing skills
    sorted_missing = sorted(missing.items(), key=lambda x: x[1])
    
    # Find items with overshoot to replace
    overshoot_items = []
    slot_overshoot_counts = {}
    
    for piece in loadout:
        current_skills = piece.get('skills', [])
        piece_overshoots = [s for s in current_skills if s in overshoot and s != 'all']
        if piece_overshoots:
            overshoot_items.append((piece, piece_overshoots))
            slot = piece['slot']
            slot_overshoot_counts[slot] = slot_overshoot_counts.get(slot, 0) + 1
            # Also add to global counts
            total_slot_counts[slot] = total_slot_counts.get(slot, 0) + 1
    
    if overshoot_items:
        print("\n  Consider replacing these overshoot items:")
        for piece, piece_overshoots in overshoot_items:
            gear_name = piece.get('name', f"Item {piece['id']}")
            print(f"   - [{piece['slot']:8}] {gear_name} (has overshoot: {', '.join(piece_overshoots)})")
    
    print("\n  Recommended skill combinations:")
    for i, (skill1, _) in enumerate(sorted_missing):
        for skill2, _ in sorted_missing[i:]:
            key = tuple(sorted((skill1, skill2)))
            if key in shown:
                continue
            shown.add(key)
            print(f"   - ({skill1} + {skill2})")
            if len(shown) >= 5:
                break
        if len(shown) >= 5:
            break


def print_final_recommendations():
    global total_slot_counts, total_all_solutions, total_slot_skills

    if not total_slot_counts:
        return

    print("\n" + "="*60)
    print("📊 OVERALL RECOMMENDATIONS ACROSS ALL COMBINATIONS")
    print("="*60)

    print("\nSlot replacement frequency (total across all combinations):")
    for slot, count in sorted(total_slot_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {slot}: {count} possible replacement(s)")
        if slot in total_slot_skills:
            for pair, freq in sorted(total_slot_skills[slot].items(), key=lambda x: x[1], reverse=True):
                print(f"      — ({pair[0]} + {pair[1]}): {freq}x")

    total_slot_counts.clear()
    total_all_solutions.clear()
    total_slot_skills.clear()




def analyse_unused_gear():
    """Analyse which gear pieces are never used in any optimal combination."""
    
    # Re-run the optimizer to get best combinations
    best_deficit = float("inf")
    best = []

    for loadout in generate_loadouts():
        deficit, overshoot, totals, diff_map = evaluate(loadout)

        if deficit < best_deficit:
            best_deficit = deficit
            best = [(loadout, overshoot, totals, diff_map)]
        elif deficit == best_deficit:
            best.append((loadout, overshoot, totals, diff_map))

    best.sort(key=lambda x: x[1])
    min_overshoot = best[0][1]
    best = [b for b in best if b[1] == min_overshoot]

    # Collect all gear IDs that appear in any optimal combination
    used_ids = set()
    for loadout, _, _, _ in best:
        for piece in loadout:
            used_ids.add(piece["id"])

    # Find unused gear
    unused = [g for g in GEAR if g["id"] not in used_ids]

    print("\n" + "="*60)
    print("♻️  GEAR RECYCLE ANALYSIS")
    print("="*60)

    if not unused:
        print("\n  ✅ All gear is used in at least one optimal combination.")
    else:
        print(f"\n  🗑️  {len(unused)} piece(s) never appear in any optimal combination:\n")
        for piece in unused:
            skills_str = " + ".join(piece["skills"].keys())
            print(f"    • [{piece['slot']:8}] {GEAR_NAMES[piece['id']]}  ({skills_str})")

    print(f"\n  📦 Gear used in at least one optimal combination ({len(used_ids)}/{len(GEAR)}):\n")
    for piece in GEAR:
        if piece["id"] in used_ids:
            skills_str = " + ".join(piece["skills"].keys())
            print(f"    • [{piece['slot']:8}] {GEAR_NAMES[piece['id']]}  ({skills_str})")
# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def find_best():
    print("=== SMART GEAR OPTIMIZER ===\n")

    best_deficit = float("inf")
    best = []

    for loadout in generate_loadouts():
        deficit, overshoot, totals, diff_map = evaluate(loadout)

        if deficit < best_deficit:
            best_deficit = deficit
            best = [(loadout, overshoot, totals, diff_map)]
        elif deficit == best_deficit:
            best.append((loadout, overshoot, totals, diff_map))

    # Now refine by overshoot
    best.sort(key=lambda x: x[1])
    min_overshoot = best[0][1]
    best = [b for b in best if b[1] == min_overshoot]

    print(f"Best deficit: {best_deficit}")
    print(f"Best overshoot: {min_overshoot}")
    print(f"Found {len(best)} best combination(s)\n")

    for i, (loadout, overshoot, totals, diff_map) in enumerate(best):
        print(f"--- Combination {i+1} ---")

        for piece in loadout:
            print(f"[{piece['slot']:8}] {GEAR_NAMES[piece['id']]}")

        print("\nTotals:")
        for s in ALL_SKILLS:
            print(f"{s:15}: {totals[s]} ({diff_map[s]:+})")


        print()

        suggest_per_combination(loadout, diff_map)
    


    


if __name__ == "__main__":
    find_best()
    print_final_recommendations()
    analyse_unused_gear()