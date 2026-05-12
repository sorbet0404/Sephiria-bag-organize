# logic.py
import re
import random
import math
from data import SLABS_DATA, ARTIFACTS_DATA

# ──────────────────────────────────────────────
# 빌드 우선순위 / 스탯 파싱 및 타격형 아티팩트 정의
# ──────────────────────────────────────────────

ALL_STATS = [
    '치명타 확률', '얼음속성 피해', '공격 속도', '회피', '물리 피해',
    '화염속성 피해', '번개속성 피해', '치명타 피해', '방어력', '이동 속도',
    '최대 MP', 'MP 재생', '최대 HP', '모든 피해 증폭', '마법서 가속',
    '가장 높은 속성 피해', '마법서 피해량', '얼음무구 피해량', '행운',
    '고정 피해', '먹구름 소모 속도', '특수 공격 피해', '일반 공격 피해',
    '대시 회복 속도', '대시 횟수', '보호막', '태양검 피해량', '소용돌이 범위',
    '먹구름 회복 속도', '먹구름 용량', '마법 가속', 'MP 흡수', '최종 무기 공격력',
    '먹구름 추가 피해량', '화상 피해량', '동료 피해량', '대시 공격 피해',
    '가시', '동료 부활 가속', '얼음무구 충전 속도', '무기 피해량',
    '소용돌이 피해', '협상력',
]

DIRECT_ATTACK_ARTIFACTS = {
    '노란 행성', '붉은 행성', '푸른 행성', '하얀 행성', '하늘색 행성', '암흑 행성', '잿빛 행성',
    '차크람', '전격 차크람', '쿠나이', '팔라스의 카드', '얼어붙은 활',
    '붉은 뱀의 눈', '볼루스파', '테로의 영혼 가루', '아마드의 영혼 가루', '헤이타의 영혼 가루',
    '미니 발리스타', '금빛 핸드벨', '채굴작업 총괄 완장'
}

_STAT_PATTERNS = [
    (r'물리 피해', '물리 피해'),
    (r'화염\s*속성\s*피해', '화염속성 피해'),
    (r'얼음\s*속성\s*피해', '얼음속성 피해'),
    (r'번개\s*속성\s*피해', '번개속성 피해'),
    (r'가장 높은 속성 피해', '가장 높은 속성 피해'),
    (r'치명타 확률', '치명타 확률'),
    (r'치명타 피해', '치명타 피해'),
    (r'공격 속도', '공격 속도'),
    (r'이동 속도', '이동 속도'),
    (r'방어력', '방어력'),
    (r'회피', '회피'),
    (r'최대 HP', '최대 HP'),
    (r'최대 MP', '최대 MP'),
    (r'MP 재생', 'MP 재생'),
    (r'MP 흡수', 'MP 흡수'),
    (r'마법서 피해량', '마법서 피해량'),
    (r'마법서 가속', '마법서 가속'),
    (r'마법 가속', '마법 가속'),
    (r'대시 회복 속도', '대시 회복 속도'),
    (r'무기 피해량', '무기 피해량'),
    (r'최종 무기 공격력', '최종 무기 공격력'),
    (r'동료.*피해량|동료가 입히는 피해량', '동료 피해량'),
    (r'동료.*방어력', '동료 방어력'),
    (r'동료.*부활 시간', '동료 부활 가속'),
    (r'먹구름 용량', '먹구름 용량'),
    (r'먹구름.*회복 속도', '먹구름 회복 속도'),
    (r'먹구름.*소모 속도', '먹구름 소모 속도'),
    (r'먹구름.*추가 피해량', '먹구름 추가 피해량'),
    (r'행성 피해량|행성.*피해', '행성 피해량'),
    (r'행성 공격 속도', '행성 공격 속도'),
    (r'얼음무구.*피해량|얼음 무구.*피해량', '얼음무구 피해량'),
    (r'얼음무구.*충전 속도|얼음 무구.*충전 속도', '얼음무구 충전 속도'),
    (r'태양검 피해량', '태양검 피해량'),
    (r'화상.*피해량', '화상 피해량'),
    (r'화상.*공격 속도', '화상 공격 속도'),
    (r'모든 피해 증폭', '모든 피해 증폭'),
    (r'일반 공격 피해', '일반 공격 피해'),
    (r'특수 공격 피해', '특수 공격 피해'),
    (r'대시 공격 피해', '대시 공격 피해'),
    (r'소용돌이 피해', '소용돌이 피해'),
    (r'소용돌이 범위', '소용돌이 범위'),
    (r'고정 피해', '고정 피해'),
    (r'대시 횟수', '대시 횟수'),
    (r'보호막', '보호막'),
    (r'HP 흡수', 'HP 흡수'),
    (r'행운', '행운'),
    (r'가시', '가시'),
    (r'협상력', '협상력'),
]

_stat_cache = {}
_level_stat_cache = {}

def get_artifact_level_stats(name):
    if name in _level_stat_cache:
        return _level_stat_cache[name]

    item = ARTIFACTS_DATA.get(name)
    if not item:
        _level_stat_cache[name] = {}
        return {}

    result = {}
    for line in item.get('effect', '').split('\n'):
        if 'X' in line:
            continue
        matches = re.findall(r'([+-]?[\d.]+(?:/[\d.]+)+)', line)
        for m in matches:
            parts = m.split('/')
            try:
                values = [float(p) for p in parts]
            except ValueError:
                continue
            if len(values) < 2:
                continue
            for pattern, stat_name in _STAT_PATTERNS:
                if re.search(pattern, line):
                    if stat_name not in result:
                        result[stat_name] = values
                    break

    _level_stat_cache[name] = result
    return result

def _is_increasing(values_str):
    try:
        parts = [float(x) for x in values_str.split('/')]
        return len(parts) >= 2 and parts[-1] > parts[0]
    except:
        return False

def get_artifact_stats(name):
    if name in _stat_cache:
        return _stat_cache[name]
    item = ARTIFACTS_DATA.get(name)
    if not item:
        _stat_cache[name] = []
        return []
    found = []
    for line in item.get('effect', '').split('\n'):
        nums = re.findall(r'[\d.]+(?:/[\d.]+)+', line)
        if not any(_is_increasing(n) for n in nums):
            continue
        for pattern, stat_name in _STAT_PATTERNS:
            if re.search(pattern, line):
                found.append(stat_name)
                break
    _stat_cache[name] = found
    return found

def calc_build_bonus(artifact_name, build_priorities):
    if not build_priorities:
        return 0.0
    stats = get_artifact_stats(artifact_name)
    weights = {}
    for rank, w in [('1순위', 3.0), ('2순위', 2.0), ('3순위', 1.0)]:
        val = build_priorities.get(rank)
        if val and val != '없음':
            weights[val] = w
    if not weights:
        return 0.0
    bonus = sum(weights[s] for s in stats if s in weights)
    if bonus == 0.0 and stats:
        return -0.5
    return bonus

def get_offs(name, r, c, rot, rows, cols, locked=None):
    s = SLABS_DATA.get(name)
    if not s: return []
    def rotate_coord(dr, dc, k):
        for _ in range(k): dr, dc = dc, -dr
        return dr, dc
    
    off_type = s['off']
    actual_rot = 0 if s.get('nr') else rot
    ignore_flag = s.get('ignore_type', False)
    
    max_r = rows - 1
    if locked is not None:
        unlocked_rows = [i for i in range(rows) if not all(locked[i])]
        if unlocked_rows: max_r = max(unlocked_rows)
    
    res = []
    
    if off_type == 'row': 
        res = [{'dr': 0, 'dc': nc - c, 'val': s['v']} for nc in range(cols) if nc != c]
    elif off_type in ('col', 'col_all'): 
        res = [{'dr': nr - r, 'dc': 0, 'val': 1} for nr in range(rows) if nr != r]
    elif off_type == 'bottom_row': 
        res = [{'dr': max_r - r, 'dc': nc - c, 'val': 1} for nc in range(cols)]
    elif off_type == 'diag_right':
        for d in range(1, max(rows, cols)):
            if r - d >= 0 and c + d < cols: res.append({'dr': -d, 'dc': d, 'val': 1})
            if r + d < rows and c - d >= 0: res.append({'dr': d, 'dc': -d, 'val': 1})
    elif off_type == 'border_rows':
        for nc in range(cols):
            res.append({'dr': -r, 'dc': nc - c, 'val': 1})
            res.append({'dr': max_r - r, 'dc': nc - c, 'val': 1})
    elif off_type == 'cross_pm':
        res = [{'dr': 0, 'dc': nc - c, 'val': 1} for nc in range(cols) if nc != c]
        res += [{'dr': nr - r, 'dc': 0, 'val': -1} for nr in range(rows) if nr != r]
    elif off_type == 'cross_all':
        res = [{'dr': 0, 'dc': nc - c, 'val': 1} for nc in range(cols) if nc != c]
        res += [{'dr': nr - r, 'dc': 0, 'val': 1} for nr in range(rows) if nr != r]
    elif off_type == 'row_minus_up3':
        res = [{'dr': 0, 'dc': nc - c, 'val': -1} for nc in range(cols) if nc != c]
        if r - 1 >= 0: res.append({'dr': -1, 'dc': 0, 'val': 3})
        
    elif off_type == 'row_and_ud2':
        if actual_rot % 2 == 0:
            res = [{'dr': 0, 'dc': nc - c, 'val': 1} for nc in range(cols) if nc != c]
            for dr in [-2, -1, 1, 2]:
                if 0 <= r + dr < rows: res.append({'dr': dr, 'dc': 0, 'val': 2})
        else:
            res = [{'dr': nr - r, 'dc': 0, 'val': 1} for nr in range(rows) if nr != r]
            for dc in [-2, -1, 1, 2]:
                if 0 <= c + dc < cols: res.append({'dr': 0, 'dc': dc, 'val': 2})
                
    elif off_type == 'diag_near_far':
        for d in range(1, max(rows, cols)):
            val = 2 if d == 1 else 1
            for dr, dc in [(-d, -d), (-d, d), (d, -d), (d, d)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    res.append({'dr': dr, 'dc': dc, 'val': val})
                    
    elif isinstance(off_type, list):
        for i, (dr, dc) in enumerate(off_type):
            ndr, ndc = rotate_coord(dr, dc, actual_rot)
            val = s['v'][i] if isinstance(s['v'], list) else s['v']
            res.append({'dr': ndr, 'dc': ndc, 'val': val})

    for o in res: o['ignore'] = ignore_flag
    return res

def get_dynamic_sets(name, r, c, base_sets, calges_mapping=None):
    if name == '캘세더니 열쇠':
        if calges_mapping: return [calges_mapping.get(r, '견고')]
        else: return ['견고']
    if name == '대립의 천칭': return ['잉걸불'] if c < 3 else ['빙하']
    if name == '영원의 식': return ['얼음무구'] if c < 3 else ['태양검']
    return base_sets

def get_tooltip_data(name, r, c, rows, cols, locked=None, calges_mapping=None, is_ignored=False, grid_data=None):
    item_data = ARTIFACTS_DATA.get(name)
    if not item_data: return None

    title = name
    base_sets = item_data.get('sets', [])
    dynamic_sets = get_dynamic_sets(name, r, c, base_sets, calges_mapping)
    combo_text = "✨ " + ", ".join(dynamic_sets) if dynamic_sets else ""
    
    grade = item_data.get('g', '일반')
    grade_text = f"{grade} 아티팩트"
    flavor_text = item_data.get('description', '')

    desc_lines = []
    cond = item_data.get('cond')
    
    if cond and not is_ignored:
        min_r, max_r, min_c, max_c = 0, rows - 1, 0, cols - 1
        if locked is not None:
            unlocked_rows = [i for i in range(rows) if not all(locked[i])]
            unlocked_cols = [j for j in range(cols) if not all(locked[:, j])]
            if unlocked_rows: min_r, max_r = min(unlocked_rows), max(unlocked_rows)
            if unlocked_cols: min_c, max_c = min(unlocked_cols), max(unlocked_cols)

        if cond == 'bottom' and r != max_r: desc_lines.append("⚠ 최하단 행에만 배치 가능")
        if cond == 'top' and r != min_r: desc_lines.append("⚠ 최상단 행에만 배치 가능")
        if cond == 'edge' and (c != min_c and c != max_c): desc_lines.append("⚠ 좌끝 또는 우끝 열에만 배치 가능")
        if cond == 'inside' and (r == min_r or r == max_r or c == min_c or c == max_c): desc_lines.append("⚠ 인벤토리 안쪽에만 배치 가능")
        if cond == 'both_empty':
            left_empty = (c == 0 or (grid_data is not None and not grid_data[r][c-1]))
            right_empty = (c == cols-1 or (grid_data is not None and not grid_data[r][c+1]))
            if not (left_empty and right_empty):
                desc_lines.append("⚠ 좌우 양쪽 칸이 모두 비어있어야 효과 발동")

    effect = item_data.get('effect')
    if effect: desc_lines.append(effect)

    if '행성' in dynamic_sets and grid_data is not None:
        has_telescope = False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if grid_data[nr][nc] == '거대 망원경':
                        has_telescope = True
                        break
            if has_telescope: break
        if has_telescope:
            desc_lines.append("🔭 [거대 망원경 적용됨] 투사체 거대화 및 피해량 +50% 증가!")

    if name == '하얀 종이' and grid_data is not None:
        if c > 0 and c < cols - 1:
            left_item = grid_data[r][c-1]
            right_item = grid_data[r][c+1]
            if left_item in ARTIFACTS_DATA and right_item in ARTIFACTS_DATA:
                left_sets = get_dynamic_sets(left_item, r, c-1, ARTIFACTS_DATA[left_item].get('sets', []), calges_mapping)
                right_sets = get_dynamic_sets(right_item, r, c+1, ARTIFACTS_DATA[right_item].get('sets', []), calges_mapping)
                common_sets = set(left_sets) & set(right_sets)
                if common_sets:
                    desc_lines.append(f"📄 [하얀 종이 적용됨] {', '.join(common_sets)} 콤보 +1 증가!")

    desc_text = "\n".join(desc_lines)
    return title, combo_text, desc_text, grade_text, flavor_text, grade

def calculate_active_combos(grid_data, rows, cols, combos_data, artifacts_data, calges_mapping=None):
    set_counts = {}
    
    for r in range(rows):
        for c in range(cols):
            item_name = grid_data[r][c]
            if item_name in artifacts_data:
                base_sets = artifacts_data[item_name].get('sets', [])
                dynamic_sets = get_dynamic_sets(item_name, r, c, base_sets, calges_mapping)
                for s in dynamic_sets:
                    set_counts[s] = set_counts.get(s, 0) + 1

    for r in range(rows):
        for c in range(cols):
            if grid_data[r][c] == '하얀 종이':
                if c > 0 and c < cols - 1:
                    left_item = grid_data[r][c-1]
                    right_item = grid_data[r][c+1]
                    if left_item in artifacts_data and right_item in artifacts_data:
                        left_sets = get_dynamic_sets(left_item, r, c-1, artifacts_data[left_item].get('sets', []), calges_mapping)
                        right_sets = get_dynamic_sets(right_item, r, c+1, artifacts_data[right_item].get('sets', []), calges_mapping)
                        common_sets = set(left_sets) & set(right_sets)
                        for s in common_sets:
                            set_counts[s] = set_counts.get(s, 0) + 1
                            
    for r in range(rows):
        for c in range(cols):
            if grid_data[r][c] == '북향의 금빛 침':
                if r > 0:
                    above_item = grid_data[r-1][c]
                    if above_item in DIRECT_ATTACK_ARTIFACTS:
                        above_sets = get_dynamic_sets(above_item, r-1, c, artifacts_data[above_item].get('sets', []), calges_mapping)
                        for s in above_sets:
                            set_counts[s] = set_counts.get(s, 0) + 1

    active_effects = {}
    for combo_name, count in set_counts.items():
        if combo_name in combos_data:
            active_effects[combo_name] = {"count": count, "effects": []}
            for req_count, effect in combos_data[combo_name].items():
                if count >= req_count:
                    active_effects[combo_name]["effects"].append(f"[{req_count}] {effect}")
    return active_effects

# --- 알고리즘(Simulated Annealing) 파트 ---
def evaluate_state(grid, rotations, current_levels, mystery_buffs, locked, rows, cols, build_priorities=None):
    score = 0
    penalty = 0
    
    unlocked_rows = [i for i in range(rows) if not all(locked[i])]
    unlocked_cols = [j for j in range(cols) if not all(locked[:, j])]
    if not unlocked_rows or not unlocked_cols: return 0
    min_r, max_r = min(unlocked_rows), max(unlocked_rows)
    min_c, max_c = min(unlocked_cols), max(unlocked_cols)

    slab_buffs = [[0]*cols for _ in range(rows)]
    ignored_cells = set()

    for r in range(rows):
        for c in range(cols):
            if locked[r, c]: continue
            val = grid[r, c]
            if val in SLABS_DATA:
                offs = get_offs(val, r, c, rotations[r, c], rows, cols, locked)
                for o in offs:
                    nr, nc = r + o['dr'], c + o['dc']
                    if 0 <= nr < rows and 0 <= nc < cols and not locked[nr, nc]:
                        slab_buffs[nr][nc] += o['val']
                        if o.get('ignore', False): ignored_cells.add((nr, nc))
                            
    for r in range(rows):
        for c in range(cols):
            if locked[r, c]: continue
            val = grid[r, c]
            if not val: continue 
            
            is_ignored = (r, c) in ignored_cells
            
            if val in SLABS_DATA:
                cond = SLABS_DATA[val].get('cond')
                if cond and not is_ignored:
                    if cond == 'bottom' and r != max_r: penalty += 1
                    elif cond == 'top' and r != min_r: penalty += 1
                    elif cond == 'edge' and (c != min_c and c != max_c): penalty += 1
                    elif cond == 'inside' and (r == min_r or r == max_r or c == min_c or c == max_c): penalty += 1
                    elif cond == 'both_empty':
                        left_empty = (c == 0 or not grid[r, c-1])
                        right_empty = (c == cols-1 or not grid[r, c+1])
                        if not (left_empty and right_empty): penalty += 1
                    
            elif val in ARTIFACTS_DATA:
                # [수정됨] 신비 버프 여부에 따라 2배만 적용되도록 수정
                myst_val = mystery_buffs[r, c]
                myst_mult = 2 if myst_val > 0 else 1
                
                base_lv = int(current_levels[r][c]) + slab_buffs[r][c]
                total_lv = base_lv * myst_mult  # 2배 곱연산
                
                # 아티팩트의 최종 레벨을 점수에 반영
                score += total_lv
                
                if build_priorities:
                    level_stats = get_artifact_level_stats(val)
                    weights = {}
                    for rank, w in [('1순위', 3.0), ('2순위', 2.0), ('3순위', 1.0)]:
                        v = build_priorities.get(rank)
                        if v and v != '없음':
                            weights[v] = w
                    for stat_name, values in level_stats.items():
                        if stat_name in weights:
                            max_lv = len(values) - 1
                            actual_lv = min(max(total_lv, 0), max_lv)
                            score += values[actual_lv] * weights[stat_name]

                    build_bonus = calc_build_bonus(val, build_priorities)
                    score += build_bonus * 10
                
                cond = ARTIFACTS_DATA[val].get('cond')
                if cond and not is_ignored:
                    if cond == 'bottom' and r != max_r: penalty += 1
                    elif cond == 'top' and r != min_r: penalty += 1
                    elif cond == 'edge' and (c != min_c and c != max_c): penalty += 1
                    elif cond == 'inside' and (r == min_r or r == max_r or c == min_c or c == max_c): penalty += 1
                    elif cond == 'both_empty':
                        left_empty = (c == 0 or not grid[r, c-1])
                        right_empty = (c == cols-1 or not grid[r, c+1])
                        if not (left_empty and right_empty): penalty += 1
                    
                if val == '거대 망원경':
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and not locked[nr, nc]:
                                target = grid[nr, nc]
                                if target in ARTIFACTS_DATA:
                                    sets = ARTIFACTS_DATA[target].get('sets', [])
                                    if not sets and 'set' in ARTIFACTS_DATA[target]:
                                        sets = [ARTIFACTS_DATA[target]['set']]
                                    if '행성' in sets:
                                        score += 500 

                if val == '북향의 금빛 침':
                    if r > 0 and not locked[r-1, c]:
                        above = grid[r-1, c]
                        if above in DIRECT_ATTACK_ARTIFACTS:
                            score += 300

                if val == '하얀 종이':
                    if c > 0 and c < cols - 1:
                        left_item = grid[r, c-1]
                        right_item = grid[r, c+1]
                        if left_item in ARTIFACTS_DATA and right_item in ARTIFACTS_DATA:
                            left_sets = get_dynamic_sets(left_item, r, c-1, ARTIFACTS_DATA[left_item].get('sets', []))
                            right_sets = get_dynamic_sets(right_item, r, c+1, ARTIFACTS_DATA[right_item].get('sets', []))
                            if set(left_sets) & set(right_sets):
                                score += 300 
                                        
    return score - (penalty * 10000)

def optimize_layout(initial_grid, initial_rotations, initial_levels, mystery_buffs, locked, rows, cols, build_priorities=None):
    current_grid = initial_grid.copy()
    current_rotations = initial_rotations.copy()
    current_levels = initial_levels.copy()
    
    movable_pos = [(r, c) for r in range(rows) for c in range(cols) if not locked[r, c]]
    if len(movable_pos) < 2: return initial_grid.tolist(), initial_rotations.tolist(), initial_levels.tolist()
        
    current_score = evaluate_state(current_grid, current_rotations, current_levels, mystery_buffs, locked, rows, cols, build_priorities)
    
    best_grid = current_grid.copy()
    best_rotations = current_rotations.copy()
    best_levels = current_levels.copy()
    best_score = current_score
    
    T = 200.0
    T_min = 0.1
    alpha = 0.995
    
    while T > T_min:
        for _ in range(50):
            action = random.choice(['swap', 'rotate'])
            next_grid = current_grid.copy()
            next_rotations = current_rotations.copy()
            next_levels = current_levels.copy()
            
            if action == 'swap':
                p1, p2 = random.sample(movable_pos, 2)
                r1, c1 = p1
                r2, c2 = p2
                next_grid[r1, c1], next_grid[r2, c2] = next_grid[r2, c2], next_grid[r1, c1]
                next_rotations[r1, c1], next_rotations[r2, c2] = next_rotations[r2, c2], next_rotations[r1, c1]
                next_levels[r1, c1], next_levels[r2, c2] = next_levels[r2, c2], next_levels[r1, c1]
            else:
                r1, c1 = random.choice(movable_pos)
                val = next_grid[r1, c1]
                if val in SLABS_DATA and not SLABS_DATA[val].get('nr'):
                    next_rotations[r1, c1] = (next_rotations[r1, c1] + random.choice([1, 2, 3])) % 4
                else: continue
                    
            next_score = evaluate_state(next_grid, next_rotations, next_levels, mystery_buffs, locked, rows, cols, build_priorities)
            
            if next_score > current_score:
                accept = True
            else:
                delta = next_score - current_score
                accept = random.random() < math.exp(delta / T)
                
            if accept:
                current_grid = next_grid
                current_rotations = next_rotations
                current_levels = next_levels
                current_score = next_score
                
                if current_score > best_score:
                    best_grid = current_grid.copy()
                    best_rotations = current_rotations.copy()
                    best_levels = current_levels.copy()
                    best_score = current_score
        T *= alpha
        
    return best_grid.tolist(), best_rotations.tolist(), best_levels.tolist()