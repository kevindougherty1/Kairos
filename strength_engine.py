# STRENGTH ENGINE V1
# MEV-default resistance programming coordinated with the running plan.
# Design decisions locked 2026-07-18 (see KAIROS_CONTEXT.md):
# - MEV framework: 2-4 working sets per movement, high proximity to failure,
#   compound + stretch-biased isolation pairing, ~6-12 hard sets/muscle/week.
# - Volume knob (recovery) scales sets; emphasis knob shifts rep ranges.
# - Engine picks lifts; user swaps within movement pattern (swap_options()).
# - Double progression at fixed cadence: top of rep range at target RIR on
#   all sets -> add load next session, drop to bottom of range.
# - Scheduling style is a user preference: "stack" (hard days hard) or
#   "stagger" (strength on easy/rest days, never the day before a hard run).

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

EXPERIENCES = ["beginner", "intermediate", "advanced"]

# Running-plan phases (HM uses "Specific", marathon uses "Peak") mapped onto
# the strength phases that drive prescription.
PHASE_MAP = {
    "Base": "Base",
    "Build": "Build",
    "Specific": "Maintenance",
    "Peak": "Maintenance",
    "Taper": "Deload",
    "Race": "Race",
}

# What the user's equipment choice actually grants access to. A barbell
# implies a full gym; dumbbells imply a home setup; bodyweight is bodyweight.
EQUIPMENT_ACCESS = {
    "barbell": {"barbell", "dumbbell", "cable", "machine", "bodyweight"},
    "dumbbell": {"dumbbell", "bodyweight"},
    "bodyweight": {"bodyweight"},
}

# Running-schedule day names that are NOT hard days ("Z2" is the marathon
# engine's label for easy runs).
NON_HARD_RUN_NAMES = {"Rest", "Easy", "Z2", "Shakeout"}


# -----------------------------
# LIFT LIBRARY
# -----------------------------
# Curated, not exhaustive. Tags:
#   pattern    - movement pattern for swap logic and template slots
#   bias       - stretch / peak / mid (drives stretch-biased isolation pairing)
#   equipment  - list of equipment that can perform the lift
#   difficulty - beginner_safe / needs_technique / spotter_recommended
#   compound   - True for multi-joint anchors, False for isolations
#   muscle     - only set for accessory-pattern lifts (slot targeting)
#   time_based - dose is time/distance, not reps
#   regression - an assisted / scaled-down substitute for a harder version of
#                the same movement. Still selectable when it genuinely ranks
#                best, but kept out of the widened rotation tier for anyone
#                past beginner: rotating a capable lifter into the assisted
#                variant of a movement they can already do is a downgrade,
#                not variety.

def lift(name, pattern, bias, equipment, difficulty, compound, muscle=None, time_based=False,
         dose=None, regression=False):
    return {
        "name": name,
        "pattern": pattern,
        "bias": bias,
        "equipment": equipment,
        "difficulty": difficulty,
        "compound": compound,
        "muscle": muscle,
        "time_based": time_based,
        "dose": dose,
        "regression": regression,
    }


LIFT_LIBRARY = [
    # --- squat ---
    lift("Back Squat", "squat", "mid", ["barbell"], "needs_technique", True),
    lift("Front Squat", "squat", "mid", ["barbell"], "needs_technique", True),
    lift("Goblet Squat", "squat", "mid", ["dumbbell"], "beginner_safe", True),
    lift("Leg Press", "squat", "mid", ["machine"], "beginner_safe", True),
    lift("Hack Squat", "squat", "stretch", ["machine"], "beginner_safe", True),
    lift("Bulgarian Split Squat", "squat", "stretch", ["dumbbell", "bodyweight"], "beginner_safe", True),
    lift("Walking Lunge", "squat", "stretch", ["dumbbell", "bodyweight"], "beginner_safe", True),
    lift("Step-Up", "squat", "mid", ["dumbbell", "bodyweight"], "beginner_safe", True),
    lift("Bodyweight Squat", "squat", "mid", ["bodyweight"], "beginner_safe", True),
    lift("Leg Extension", "squat", "peak", ["machine"], "beginner_safe", False),

    # --- hinge ---
    lift("Conventional Deadlift", "hinge", "mid", ["barbell"], "needs_technique", True),
    lift("Trap Bar Deadlift", "hinge", "mid", ["barbell"], "beginner_safe", True),
    lift("Romanian Deadlift", "hinge", "stretch", ["barbell"], "needs_technique", True),
    lift("DB Romanian Deadlift", "hinge", "stretch", ["dumbbell"], "beginner_safe", True),
    lift("Barbell Hip Thrust", "hinge", "peak", ["barbell"], "beginner_safe", True),
    lift("Single-Leg RDL", "hinge", "stretch", ["dumbbell", "bodyweight"], "needs_technique", True),
    lift("Glute Bridge", "hinge", "peak", ["bodyweight"], "beginner_safe", True),
    lift("Back Extension", "hinge", "mid", ["bodyweight", "machine"], "beginner_safe", False),
    lift("Seated Leg Curl", "hinge", "stretch", ["machine"], "beginner_safe", False),
    lift("Nordic Ham Curl", "hinge", "stretch", ["bodyweight"], "needs_technique", False),
    lift("Assisted Nordic Curl", "hinge", "stretch", ["bodyweight"], "beginner_safe", False, regression=True),

    # --- horizontal push ---
    lift("Barbell Bench Press", "horizontal_push", "mid", ["barbell"], "spotter_recommended", True),
    lift("Incline DB Press", "horizontal_push", "stretch", ["dumbbell"], "beginner_safe", True),
    lift("Flat DB Press", "horizontal_push", "stretch", ["dumbbell"], "beginner_safe", True),
    lift("Incline Barbell Bench Press", "horizontal_push", "stretch", ["barbell"], "spotter_recommended", True),
    lift("Machine Chest Press", "horizontal_push", "mid", ["machine"], "beginner_safe", True),
    lift("Cable Fly", "horizontal_push", "stretch", ["cable"], "beginner_safe", False),
    lift("Pec Deck Fly", "horizontal_push", "stretch", ["machine"], "beginner_safe", False),
    lift("DB Fly", "horizontal_push", "stretch", ["dumbbell"], "beginner_safe", False),
    lift("Push-Up", "horizontal_push", "mid", ["bodyweight"], "beginner_safe", True),
    lift("Deficit Push-Up", "horizontal_push", "stretch", ["bodyweight"], "beginner_safe", True),
    lift("Dip", "horizontal_push", "stretch", ["bodyweight"], "needs_technique", True),

    # --- vertical push ---
    lift("Overhead Press", "vertical_push", "mid", ["barbell"], "needs_technique", True),
    lift("Seated DB Shoulder Press", "vertical_push", "mid", ["dumbbell"], "beginner_safe", True),
    lift("Machine Shoulder Press", "vertical_push", "mid", ["machine"], "beginner_safe", True),
    lift("Pike Push-Up", "vertical_push", "mid", ["bodyweight"], "beginner_safe", True),
    lift("DB Lateral Raise", "vertical_push", "peak", ["dumbbell"], "beginner_safe", False),
    lift("Cable Lateral Raise", "vertical_push", "stretch", ["cable"], "beginner_safe", False),

    # --- horizontal pull ---
    lift("Barbell Row", "horizontal_pull", "mid", ["barbell"], "needs_technique", True),
    lift("One-Arm DB Row", "horizontal_pull", "stretch", ["dumbbell"], "beginner_safe", True),
    lift("Chest-Supported DB Row", "horizontal_pull", "mid", ["dumbbell"], "beginner_safe", True),
    lift("Seated Cable Row", "horizontal_pull", "stretch", ["cable"], "beginner_safe", True),
    lift("Machine Row", "horizontal_pull", "mid", ["machine"], "beginner_safe", True),
    lift("Inverted Row", "horizontal_pull", "mid", ["bodyweight"], "beginner_safe", True),

    # --- vertical pull ---
    lift("Pull-Up", "vertical_pull", "stretch", ["bodyweight"], "needs_technique", True),
    lift("Chin-Up", "vertical_pull", "stretch", ["bodyweight"], "beginner_safe", True),
    lift("Lat Pulldown", "vertical_pull", "stretch", ["cable", "machine"], "beginner_safe", True),
    lift("Assisted Pull-Up", "vertical_pull", "stretch", ["machine"], "beginner_safe", True, regression=True),

    # --- carry ---
    lift("Farmer's Carry", "carry", "mid", ["dumbbell"], "beginner_safe", True, time_based=True, dose="30-45 sec heavy walk"),
    lift("Suitcase Carry", "carry", "mid", ["dumbbell"], "beginner_safe", True, time_based=True, dose="30-45 sec per side"),
    lift("Overhead Carry", "carry", "mid", ["dumbbell"], "needs_technique", True, time_based=True, dose="20-30 sec per side"),

    # --- olympic / power ---
    lift("Power Clean", "olympic", "mid", ["barbell"], "needs_technique", True),
    lift("Hang Power Clean", "olympic", "mid", ["barbell"], "needs_technique", True),
    lift("Push Press", "olympic", "mid", ["barbell"], "needs_technique", True),
    lift("DB Snatch", "olympic", "mid", ["dumbbell"], "needs_technique", True),
    lift("DB Swing", "olympic", "mid", ["dumbbell"], "beginner_safe", True),

    # --- plyo (enters in Build phase) ---
    lift("Box Jump", "plyo", "mid", ["bodyweight"], "beginner_safe", True),
    lift("Broad Jump", "plyo", "mid", ["bodyweight"], "beginner_safe", True),
    lift("Pogo Hops", "plyo", "mid", ["bodyweight"], "beginner_safe", True),
    lift("Single-Leg Hop", "plyo", "mid", ["bodyweight"], "needs_technique", True),
    lift("Depth Jump", "plyo", "mid", ["bodyweight"], "needs_technique", True),

    # --- core ---
    lift("Plank", "core", "mid", ["bodyweight"], "beginner_safe", False, time_based=True, dose="30-60 sec"),
    lift("Side Plank", "core", "mid", ["bodyweight"], "beginner_safe", False, time_based=True, dose="30-45 sec per side"),
    lift("Dead Bug", "core", "mid", ["bodyweight"], "beginner_safe", False),
    lift("Hanging Knee Raise", "core", "stretch", ["bodyweight"], "beginner_safe", False),
    lift("Ab Wheel Rollout", "core", "stretch", ["bodyweight"], "needs_technique", False),
    lift("Cable Crunch", "core", "mid", ["cable"], "beginner_safe", False),
    lift("Pallof Press", "core", "mid", ["cable"], "beginner_safe", False),

    # --- accessory (muscle-targeted isolations) ---
    lift("Incline DB Curl", "accessory", "stretch", ["dumbbell"], "beginner_safe", False, muscle="biceps"),
    lift("Preacher Curl", "accessory", "stretch", ["dumbbell", "machine"], "beginner_safe", False, muscle="biceps"),
    lift("DB Curl", "accessory", "mid", ["dumbbell"], "beginner_safe", False, muscle="biceps"),
    lift("Hammer Curl", "accessory", "mid", ["dumbbell"], "beginner_safe", False, muscle="biceps"),
    lift("Cable Curl", "accessory", "mid", ["cable"], "beginner_safe", False, muscle="biceps"),
    lift("Overhead Cable Triceps Extension", "accessory", "stretch", ["cable"], "beginner_safe", False, muscle="triceps"),
    lift("Lying DB Triceps Extension", "accessory", "stretch", ["dumbbell"], "beginner_safe", False, muscle="triceps"),
    lift("Cable Triceps Pushdown", "accessory", "peak", ["cable"], "beginner_safe", False, muscle="triceps"),
    lift("Close-Grip Push-Up", "accessory", "mid", ["bodyweight"], "beginner_safe", False, muscle="triceps"),
    # Rear delts — the standard blind spot: lateral raises are side-delt only
    # and rows only hit them incidentally, so they get a dedicated slot.
    lift("Reverse Pec Deck", "accessory", "stretch", ["machine"], "beginner_safe", False, muscle="rear_delts"),
    lift("DB Rear Delt Fly", "accessory", "stretch", ["dumbbell"], "beginner_safe", False, muscle="rear_delts"),
    lift("Face Pull", "accessory", "peak", ["cable"], "beginner_safe", False, muscle="rear_delts"),
    lift("Prone Y-Raise", "accessory", "mid", ["bodyweight"], "beginner_safe", False, muscle="rear_delts"),
    # Hip abductors — glute medius. Matters more here than in a general
    # program: weak abductors drive knee valgus and IT band trouble in runners.
    lift("Machine Hip Abduction", "accessory", "peak", ["machine"], "beginner_safe", False, muscle="abductors"),
    lift("Cable Hip Abduction", "accessory", "peak", ["cable"], "beginner_safe", False, muscle="abductors"),
    lift("Side-Lying Hip Abduction", "accessory", "mid", ["bodyweight"], "beginner_safe", False, muscle="abductors"),
    lift("Standing Calf Raise", "accessory", "stretch", ["machine", "dumbbell", "bodyweight"], "beginner_safe", False, muscle="calves"),
    lift("Seated Calf Raise", "accessory", "stretch", ["machine"], "beginner_safe", False, muscle="calves"),
    lift("Single-Leg Calf Raise", "accessory", "stretch", ["bodyweight"], "beginner_safe", False, muscle="calves"),
    lift("Tibialis Raise", "accessory", "mid", ["bodyweight"], "beginner_safe", False, muscle="tibialis"),
    lift("Heel Walk", "accessory", "mid", ["bodyweight"], "beginner_safe", False, muscle="tibialis", time_based=True, dose="30-45 sec"),
]

PATTERNS = {e["pattern"] for e in LIFT_LIBRARY}
EQUIPMENT_TAGS = {"barbell", "dumbbell", "cable", "machine", "bodyweight"}


# -----------------------------
# SPLIT TEMPLATES
# -----------------------------
# Each split defines its session cycle. Sessions list their slots:
#   (pattern, prefer[, muscle]) where prefer is "compound" or "stretch".
# Pattern density per session is fixed per split (settled 2026-07-18):
# PPL ~2-3 patterns, upper-lower ~3-4, full-body ~4-5.

def slot(pattern, prefer, muscle=None):
    return {"pattern": pattern, "prefer": prefer, "muscle": muscle}


SPLIT_TEMPLATES = {
    "full_body": [
        {
            "name": "Full Body A",
            "leg_heavy": True,
            "slots": [
                slot("squat", "compound"),
                slot("horizontal_push", "compound"),
                slot("horizontal_pull", "compound"),
                slot("hinge", "stretch"),
                slot("core", "compound"),
            ],
        },
        {
            "name": "Full Body B",
            "leg_heavy": True,
            "slots": [
                slot("hinge", "compound"),
                slot("vertical_push", "compound"),
                slot("vertical_pull", "compound"),
                slot("squat", "stretch"),
                slot("core", "compound"),
            ],
        },
    ],
    "upper_lower": [
        {
            "name": "Upper",
            "leg_heavy": False,
            "slots": [
                slot("horizontal_push", "compound"),
                slot("horizontal_pull", "compound"),
                slot("vertical_push", "compound"),
                slot("vertical_pull", "compound"),
                slot("horizontal_push", "stretch"),
                slot("accessory", "stretch", muscle="rear_delts"),
            ],
        },
        {
            "name": "Lower",
            "leg_heavy": True,
            "slots": [
                slot("squat", "compound"),
                slot("hinge", "compound"),
                slot("hinge", "stretch"),
                slot("accessory", "stretch", muscle="abductors"),
                slot("accessory", "stretch", muscle="calves"),
                slot("core", "compound"),
            ],
        },
    ],
    "ppl": [
        {
            "name": "Push",
            "leg_heavy": False,
            "slots": [
                slot("horizontal_push", "compound"),
                slot("horizontal_push", "stretch"),
                slot("vertical_push", "compound"),
                slot("accessory", "stretch", muscle="triceps"),
            ],
        },
        {
            "name": "Pull",
            "leg_heavy": False,
            "slots": [
                slot("horizontal_pull", "compound"),
                slot("vertical_pull", "compound"),
                slot("accessory", "stretch", muscle="rear_delts"),
                slot("accessory", "stretch", muscle="biceps"),
                slot("core", "compound"),
            ],
        },
        {
            "name": "Legs",
            "leg_heavy": True,
            "slots": [
                slot("squat", "compound"),
                slot("hinge", "compound"),
                slot("hinge", "stretch"),
                slot("accessory", "stretch", muscle="abductors"),
                slot("accessory", "stretch", muscle="calves"),
                slot("core", "compound"),
            ],
        },
    ],
    "olympic_focused": [
        {
            "name": "Power A",
            "leg_heavy": True,
            "slots": [
                slot("olympic", "compound"),
                slot("squat", "compound"),
                slot("vertical_push", "compound"),
                slot("core", "compound"),
            ],
        },
        {
            "name": "Power B",
            "leg_heavy": True,
            "slots": [
                slot("olympic", "compound"),
                slot("hinge", "compound"),
                slot("vertical_pull", "compound"),
                slot("core", "compound"),
            ],
        },
    ],
    "powerlifting_focused": [
        {
            "name": "Squat Day",
            "leg_heavy": True,
            "slots": [
                slot("squat", "compound"),
                slot("squat", "stretch"),
                slot("core", "compound"),
            ],
        },
        {
            "name": "Bench Day",
            "leg_heavy": False,
            "slots": [
                slot("horizontal_push", "compound"),
                slot("horizontal_pull", "compound"),
                slot("horizontal_push", "stretch"),
                slot("accessory", "stretch", muscle="triceps"),
            ],
        },
        {
            "name": "Deadlift Day",
            "leg_heavy": True,
            "slots": [
                slot("hinge", "compound"),
                slot("vertical_pull", "compound"),
                slot("carry", "compound"),
                slot("core", "compound"),
            ],
        },
    ],
}

SPLIT_MIN_FREQUENCY = {
    "full_body": 2,
    "upper_lower": 2,
    "ppl": 3,
    "olympic_focused": 2,
    "powerlifting_focused": 3,
}


# -----------------------------
# PRESCRIPTION TABLES
# -----------------------------
# Per strength phase: rep ranges, RIR target, and the set progression across
# the phase (sets_start at phase entry -> sets_end at phase end).

PHASE_RX = {
    "Base": {
        "compound_reps": (8, 12),
        "isolation_reps": (10, 15),
        "rir": (1, 2),
        "sets_start": 2,
        "sets_end": 3,
    },
    "Build": {
        "compound_reps": (6, 10),
        "isolation_reps": (8, 12),
        "rir": (0, 1),
        "sets_start": 2,
        "sets_end": 3,
    },
    "Maintenance": {
        "compound_reps": (6, 10),
        "isolation_reps": (8, 12),
        "rir": (1, 2),
        "sets_start": 2,
        "sets_end": 2,
    },
    "Deload": {
        "compound_reps": (8, 10),
        "isolation_reps": (10, 12),
        "rir": (2, 3),
        "sets_start": 2,
        "sets_end": 2,
    },
}

# Emphasis knob shifts compound rep ranges (isolations stay hypertrophy-style;
# Deload is untouched — a deload is a deload regardless of emphasis).
EMPHASIS_COMPOUND_REPS = {
    "strength": (3, 6),
    "balanced": None,  # use phase table
    "hypertrophy": (8, 12),
}

# Per-region rep ranges. A region setting overrides both the phase table and
# the emphasis knob for every lift in that region — compounds AND isolations
# (so a chest set to 6-8 puts the fly at 6-8 too). Deload is exempt, same as
# emphasis: the taper still tapers.
REP_RANGE_OPTIONS = {"6-8": (6, 8), "8-12": (8, 12), "12-15": (12, 15)}

# "vary" cycles these across contiguous phase blocks (Base -> Build -> Peak),
# indexed by the same block ordinal that drives exercise rotation.
LEG_REP_CYCLE = [(12, 15), (6, 8), (8, 12)]

REGIONS = {"chest", "back", "shoulders", "arms", "legs"}

PATTERN_REGION = {
    "horizontal_push": "chest",
    "vertical_push": "shoulders",
    "horizontal_pull": "back",
    "vertical_pull": "back",
    "squat": "legs",
    "hinge": "legs",
}

ACCESSORY_MUSCLE_REGION = {
    "biceps": "arms",
    "triceps": "arms",
    "rear_delts": "shoulders",
    "calves": "legs",
    "tibialis": "legs",
    "abductors": "legs",
}


def lift_region(entry):
    """Body region a lift belongs to, or None if it has no region setting.

    core / carry / olympic / plyo return None and keep the phase defaults —
    they aren't the kind of work a "chest reps" style knob should govern.
    """
    if entry["pattern"] == "accessory":
        return ACCESSORY_MUSCLE_REGION.get(entry["muscle"])
    return PATTERN_REGION.get(entry["pattern"])

# Volume knob: recovery input adjusts sets per movement. MEV bounds 2-5.
RECOVERY_SET_ADJUSTMENT = {
    "fast": 1,
    "average": 0,
    "slow": -1,
}

MIN_SETS = 2
MAX_SETS = 5

RIR_CUES = {
    (0, 0): "To failure — the last rep should be a grinder.",
    (0, 1): "Push to the edge: stop when you couldn't do another clean rep.",
    (1, 2): "Hard but crisp — leave one or two clean reps in the tank.",
    (2, 3): "Deload effort — smooth and controlled, well shy of failure.",
}

PLYO_CUE = "Max intent, full recovery between sets. End the set the moment height or snap drops."

PROGRESSION_NOTE = (
    "Progression: double progression. Work within the rep range at the target RIR. "
    "When you hit the top of the range on every set while honoring the RIR, "
    "add load next session and start again at the bottom of the range."
)


# -----------------------------
# LIFT SELECTION
# -----------------------------

def allowed_lifts(pattern, equipment, muscle=None):
    access = EQUIPMENT_ACCESS[equipment]
    out = []
    for entry in LIFT_LIBRARY:
        if entry["pattern"] != pattern:
            continue
        if muscle and entry["muscle"] != muscle:
            continue
        if not any(eq in access for eq in entry["equipment"]):
            continue
        out.append(entry)
    return out


def difficulty_ok(entry, experience):
    if experience == "beginner":
        return entry["difficulty"] == "beginner_safe"
    if experience == "intermediate":
        return entry["difficulty"] != "spotter_recommended"
    return True


def select_lift(slot_def, equipment, experience, used_names, rotation_index=0,
                preferred_equipment=None):
    """Pick a lift for a template slot, rotating within the best-tied tier.

    Ranking: unused > difficulty fit > prefer-match (compound flag or stretch
    bias) > equipment order (the user's `preferred_equipment` for this slot's
    pattern wins ties if set and available; otherwise falls back to a fixed
    barbell-first default). Candidates tied on all four keys form the "top
    tier"; `rotation_index` cycles through that tier (mod its size) so a
    phase-block boundary can bring in a fresh lift without ever reaching into
    a lower-priority tier (unsafe difficulty, or a lift already used elsewhere
    this session). rotation_index=0 with no preferred_equipment always
    reproduces the single best pick, unchanged from before rotation existed.
    Falls back to a difficulty-mismatched lift (flagged) rather than leaving
    the slot empty.
    """
    candidates = allowed_lifts(slot_def["pattern"], equipment, slot_def["muscle"])
    if not candidates:
        return None, None

    prefer = slot_def["prefer"]

    def prefer_score(entry):
        if prefer == "compound":
            return 0 if entry["compound"] else 1
        # "stretch": stretch-biased isolation first, then any stretch, then rest
        if entry["bias"] == "stretch" and not entry["compound"]:
            return 0
        if entry["bias"] == "stretch":
            return 1
        return 2

    def equipment_score(entry):
        if preferred_equipment and preferred_equipment in entry["equipment"]:
            return -1
        order = ["barbell", "dumbbell", "cable", "machine", "bodyweight"]
        return min(order.index(eq) for eq in entry["equipment"] if eq in order)

    def rank(entry):
        return (
            0 if entry["name"] not in used_names else 1,
            0 if difficulty_ok(entry, experience) else 1,
            prefer_score(entry),
            equipment_score(entry),
        )

    ranked = sorted(candidates, key=rank)
    top_key = rank(ranked[0])
    top_tier = [e for e in ranked if rank(e) == top_key]

    # A slot whose best equipment tier holds exactly one lift can never rotate
    # (e.g. rear delts: DB Rear Delt Fly is the only stretch-biased dumbbell
    # option, so it would show up every week of the plan). Widen to the prefer
    # tier so the slot varies across phase blocks like every other one.
    # Skipped when the user set an equipment preference for this pattern:
    # an explicit choice outranks automatic variety.
    if len(top_tier) == 1 and not preferred_equipment:
        prefer_tier = [e for e in ranked if rank(e)[:3] == top_key[:3]]
        # Assisted/scaled variants are a downgrade for anyone who's past
        # needing them. Beginners keep them — for that audience, alternating
        # into the assisted version IS the progression path. Falls back to the
        # unfiltered tier if filtering would empty it.
        if experience != "beginner":
            prefer_tier = [e for e in prefer_tier if not e["regression"]] or prefer_tier
        if slot_def["pattern"] == "accessory":
            # Small isolation work — dumbbell vs cable vs machine vs bodyweight
            # is preference, not a loading difference. Rotate across all of it.
            top_tier = prefer_tier
        else:
            # Compound patterns — equipment tier IS a loading difference, so
            # bound how far rotation can stray. Two tiers keeps genuinely
            # comparable substitutions (barbell<->cable, cable<->bodyweight
            # pull-ups) while blocking the four-tier jump that would put a
            # full-gym lifter on Pike Push-Ups. A heuristic, not a law: the
            # equipment order is a loading proxy that inverts for vertical
            # pulls, where bodyweight is the HARDEST version, not the easiest.
            best_equip = equipment_score(prefer_tier[0])
            top_tier = [e for e in prefer_tier if equipment_score(e) <= best_equip + 2]

    chosen = top_tier[rotation_index % len(top_tier)]

    warning = None
    if not difficulty_ok(chosen, experience):
        warning = (
            f"{chosen['name']} is tagged '{chosen['difficulty']}' — no simpler {slot_def['pattern']} "
            f"option exists for your equipment. Get form checked before loading it near failure."
        )
    return chosen, warning


def swap_options(lift_name, equipment, experience=None, preferred_equipment=None):
    """Alternatives in the same movement pattern for the user's equipment.

    If preferred_equipment is set, matching alternatives are listed first.
    """
    source = next((e for e in LIFT_LIBRARY if e["name"] == lift_name), None)
    if source is None:
        raise ValueError(f"Unknown lift: {lift_name}")
    options = allowed_lifts(source["pattern"], equipment, source["muscle"])
    options = [e for e in options if e["name"] != lift_name]
    if experience:
        safe = [e for e in options if difficulty_ok(e, experience)]
        if safe:
            options = safe
    if preferred_equipment:
        options = sorted(
            options, key=lambda e: 0 if preferred_equipment in e["equipment"] else 1
        )
    return [e["name"] for e in options]


def slot_key(session_name, slot_def):
    """Stable identity for a template slot, used to key user overrides."""
    return f"{session_name}|{slot_def['pattern']}|{slot_def['prefer']}|{slot_def['muscle'] or ''}"


# -----------------------------
# PRESCRIPTION
# -----------------------------

def sets_for_position(rx, position, recovery, strength_phase):
    start, end = rx["sets_start"], rx["sets_end"]
    base = int(start + (end - start) * position + 0.5)
    if strength_phase == "Deload":
        return base  # deload volume is fixed; the knob doesn't add stress back
    adjusted = base + RECOVERY_SET_ADJUSTMENT[recovery]
    return max(MIN_SETS, min(MAX_SETS, adjusted))


def rir_for_lift(entry, rx, strength_phase):
    rir_low, rir_high = rx["rir"]
    # Stretch-biased isolations are the "take it to failure" half of the MEV
    # pairing — push them one notch closer than the compounds (never in Deload).
    if not entry["compound"] and entry["bias"] == "stretch" and strength_phase != "Deload":
        rir_low, rir_high = max(0, rir_low - 1), max(0, rir_high - 1)
    return rir_low, rir_high


def region_rep_range(entry, region_reps, strength_phase, rotation_index):
    """Rep range from the user's per-region setting, or None to fall through.

    Deload is exempt so the taper still deloads (same rule the emphasis knob
    follows). "vary" walks LEG_REP_CYCLE by phase block.
    """
    if not region_reps or strength_phase == "Deload":
        return None
    choice = region_reps.get(lift_region(entry))
    if choice is None:
        return None
    if choice == "vary":
        return LEG_REP_CYCLE[rotation_index % len(LEG_REP_CYCLE)]
    return REP_RANGE_OPTIONS[choice]


def prescribe(entry, rx, position, recovery, emphasis, strength_phase,
              region_reps=None, rotation_index=0):
    sets = sets_for_position(rx, position, recovery, strength_phase)

    if entry["pattern"] == "plyo":
        return {
            "name": entry["name"],
            "pattern": "plyo",
            "sets": min(sets, 3),
            "reps": "3-5",
            "rir": None,
            "cue": PLYO_CUE,
        }

    if entry["time_based"]:
        return {
            "name": entry["name"],
            "pattern": entry["pattern"],
            "sets": sets,
            "reps": entry["dose"],
            "rir": None,
            "cue": "Hold quality — stop the set when position breaks down.",
        }

    # Rep range by specificity: region setting > emphasis knob > phase table.
    reps = region_rep_range(entry, region_reps, strength_phase, rotation_index)
    if reps is None:
        if entry["compound"]:
            reps = rx["compound_reps"]
            override = EMPHASIS_COMPOUND_REPS[emphasis]
            if override and strength_phase != "Deload":
                reps = override
        else:
            reps = rx["isolation_reps"]

    rir_low, rir_high = rir_for_lift(entry, rx, strength_phase)
    return {
        "name": entry["name"],
        "pattern": entry["pattern"],
        "sets": sets,
        "reps": f"{reps[0]}-{reps[1]}",
        "rir": f"{rir_low}-{rir_high}" if rir_low != rir_high else str(rir_low),
        "cue": RIR_CUES[(rir_low, rir_high)],
    }


def _apply_override(slot_def, equipment, used, overrides, key, plan_warnings, session_name):
    """Look up a user-chosen lift for this slot, if one was set and still fits.

    Falls back (silently, to the caller's normal auto-select) when the override
    no longer resolves — e.g. the user changed equipment since picking it.
    """
    name = overrides.get(key)
    if name is None:
        return None
    candidates = allowed_lifts(slot_def["pattern"], equipment, slot_def["muscle"])
    entry = next((e for e in candidates if e["name"] == name and e["name"] not in used), None)
    if entry is None:
        plan_warnings.add(
            f"Your saved choice for {session_name}'s {slot_def['pattern']} slot isn't "
            f"available with your current settings — using the default pick instead."
        )
    return entry


def build_session_lifts(session_template, strength_phase, position, equipment,
                        experience, recovery, emphasis, plan_warnings, rotation_index=0,
                        overrides=None, pattern_equipment=None, region_reps=None):
    rx = PHASE_RX[strength_phase]
    used = set()
    lifts = []
    overrides = overrides or {}
    pattern_equipment = pattern_equipment or {}
    region_reps = region_reps or {}
    session_name = session_template["name"]

    slots = list(session_template["slots"])
    # Plyometrics enter in Build on leg-heavy sessions (running-specific power).
    if strength_phase == "Build" and session_template["leg_heavy"]:
        slots = [slot("plyo", "compound")] + slots

    for slot_def in slots:
        key = slot_key(session_name, slot_def)
        preferred_equipment = pattern_equipment.get(slot_def["pattern"])
        warning = None
        entry = _apply_override(slot_def, equipment, used, overrides, key, plan_warnings, session_name)
        if entry is not None and not difficulty_ok(entry, experience):
            warning = (
                f"{entry['name']} is tagged '{entry['difficulty']}' — you selected it manually; "
                f"get form checked before loading it near failure."
            )

        if entry is None:
            entry, warning = select_lift(
                slot_def, equipment, experience, used, rotation_index, preferred_equipment
            )
            if entry is None:
                # No candidate at all (e.g., olympic pattern on bodyweight):
                # substitute explosive bodyweight work rather than dropping power.
                if slot_def["pattern"] == "olympic":
                    entry, warning = select_lift(
                        slot("plyo", "compound"), equipment, experience, used, rotation_index
                    )
                    if entry is not None:
                        plan_warnings.add(
                            "No Olympic-lift option for your equipment — substituting jump work for power."
                        )
                if entry is None:
                    plan_warnings.add(
                        f"No {slot_def['pattern']} option for your equipment — slot skipped."
                    )
                    continue
        if warning:
            plan_warnings.add(warning)
        used.add(entry["name"])
        prescribed = prescribe(
            entry, rx, position, recovery, emphasis, strength_phase,
            region_reps=region_reps, rotation_index=rotation_index,
        )
        prescribed["slot_key"] = key
        prescribed["alternatives"] = swap_options(
            entry["name"], equipment, experience, preferred_equipment
        )
        lifts.append(prescribed)

    return lifts


# -----------------------------
# SCHEDULING
# -----------------------------

def run_day_name(value):
    """Normalize a schedule entry to its workout name.

    HM engine entries are dicts ({"name": ..., "miles": ...}); marathon engine
    entries are strings ("Z2 (6)", "Long Run (16)", "Rest").
    """
    if value is None:
        return "Rest"
    if isinstance(value, dict):
        return value.get("name", "Rest")
    return value.split(" (")[0]


def classify_running_days(running_schedule):
    hard, easy, rest = [], [], []
    lr_day = None
    for day in DAYS:
        name = run_day_name(running_schedule.get(day))
        if name == "Rest":
            rest.append(day)
        elif name in NON_HARD_RUN_NAMES:
            easy.append(day)
        else:
            hard.append(day)
            if name == "Long Run":
                lr_day = day
    return hard, easy, rest, lr_day


def day_before(day):
    idx = DAYS.index(day)
    return DAYS[idx - 1] if idx > 0 else None


def days_before_hard(hard_days):
    out = set()
    for day in hard_days:
        prev = day_before(day)
        if prev:
            out.add(prev)
    return out


def candidate_days(running_schedule, scheduling_style, warnings):
    """Ordered list of days to place strength sessions on, best first."""
    hard, easy, rest, lr_day = classify_running_days(running_schedule)
    before_hard = days_before_hard(hard)

    quality = [d for d in hard if d != lr_day]

    if scheduling_style == "stack":
        ordered = (
            quality
            + [d for d in rest if d not in before_hard]
            + [d for d in easy if d not in before_hard]
            + ([lr_day] if lr_day else [])
            + [d for d in rest if d in before_hard]
            + [d for d in easy if d in before_hard]
        )
    else:  # stagger
        ordered = (
            [d for d in rest if d not in before_hard]
            + [d for d in easy if d not in before_hard]
            + [d for d in rest if d in before_hard]
            + [d for d in easy if d in before_hard]
            + quality
            + ([lr_day] if lr_day else [])
        )
    return ordered, hard, lr_day, before_hard


def place_sessions(running_schedule, session_templates, scheduling_style):
    """Assign this week's strength sessions to days.

    Returns (assignments, warnings) where assignments is a list of
    (day, session_template) in chronological order.
    """
    warnings = []
    ordered, hard, lr_day, before_hard = candidate_days(running_schedule, scheduling_style, warnings)

    n = len(session_templates)
    chosen = ordered[:n]
    if len(chosen) < n:
        warnings.append(
            f"Only {len(chosen)} of {n} strength sessions could be placed this week."
        )

    if scheduling_style == "stagger":
        spilled = [d for d in chosen if d in hard]
        if spilled:
            warnings.append(
                "Not enough easy/rest days — strength placed on hard running day(s) "
                f"{', '.join(spilled)}. Run first, lift second."
            )
        risky = [d for d in chosen if d in before_hard]
        if risky:
            warnings.append(
                f"Strength on {', '.join(risky)} lands the day before a hard run — "
                "keep it honest to the RIR targets so your legs show up."
            )

    chosen.sort(key=DAYS.index)
    assignments = list(zip(chosen, session_templates))

    # Leg-heavy sessions should not sit on the long run day or the day before
    # it. Swap with a non-leg session on a safe day when possible.
    bad_days = {lr_day, day_before(lr_day) if lr_day else None} - {None}
    for i, (day, template) in enumerate(assignments):
        if template["leg_heavy"] and day in bad_days:
            for j, (other_day, other_template) in enumerate(assignments):
                if not other_template["leg_heavy"] and other_day not in bad_days:
                    assignments[i] = (day, other_template)
                    assignments[j] = (other_day, template)
                    break
            else:
                warnings.append(
                    f"Leg session lands on {day}, adjacent to the long run — "
                    "expect heavy legs; drop leg-day intensity if the long run matters more."
                )

    # A week where every day carries a run or a lift has no true rest day.
    strength_days = {day for day, _ in assignments}
    full_rest = [
        d for d in DAYS
        if run_day_name(running_schedule.get(d)) == "Rest" and d not in strength_days
    ]
    if not full_rest:
        warnings.append(
            "No full rest day this week — doable once you're used to the volume, "
            "but back off if recovery slips."
        )

    return assignments, warnings


# -----------------------------
# PLAN ORCHESTRATION
# -----------------------------

def phase_positions(running_plan):
    """Per-week (position, block_index) within contiguous engine-phase blocks.

    position is 0.0-1.0 progress through the block (drives set progression).
    block_index is the ordinal of the contiguous phase block (drives exercise
    rotation — a session template recurs across every phase of a plan, so its
    slots can pick a fresh lift each time the phase changes while staying
    fixed within one phase for double-progression trackability).
    """
    positions, block_indices = [], []
    i, block_no = 0, 0
    while i < len(running_plan):
        j = i
        while j < len(running_plan) and running_plan[j]["phase"] == running_plan[i]["phase"]:
            j += 1
        block_len = j - i
        for k in range(block_len):
            positions.append(k / (block_len - 1) if block_len > 1 else 1.0)
            block_indices.append(block_no)
        block_no += 1
        i = j
    return positions, block_indices


def default_scheduling_style(experience):
    # Beginners stagger (protect recovery while adapting); experienced runners
    # default to hard-days-hard stacking. Both remain user-overridable.
    return "stagger" if experience == "beginner" else "stack"


def build_strength_plan(running_plan, experience, split="full_body", frequency=3,
                        equipment="dumbbell", preferences=None, overrides=None,
                        pattern_equipment=None, region_reps=None):
    """Build a week-by-week strength plan coordinated with a running plan.

    running_plan: list of week dicts from either running engine (needs
    "phase" and "schedule" per week).
    overrides: optional {slot_key: lift_name} map (see slot_key()) — a
    user-chosen lift that supersedes auto-rotation for that slot, for the
    whole plan. Falls back to the normal pick (with a warning) if the named
    lift no longer fits the slot's pattern/equipment.
    pattern_equipment: optional {pattern: equipment_tag} map — a per-pattern
    equipment lean (e.g. {"squat": "machine"}) that auto-selection prefers
    when ranking candidates for that pattern, without narrowing what's
    actually available. Silently has no effect where no matching candidate
    exists (not an error — just a preference that doesn't apply here).
    region_reps: optional {region: choice} map keyed by REGIONS, where choice
    is a REP_RANGE_OPTIONS key or "vary". Overrides both the phase table and
    the emphasis knob for every lift in that region (compounds and isolations
    alike); Deload is exempt.
    Returns a list of week dicts: {week, phase, strength_phase, sessions,
    warnings, plan_warnings, notes}.
    """
    if experience not in EXPERIENCES:
        raise ValueError(f"experience must be one of {EXPERIENCES}")
    if split not in SPLIT_TEMPLATES:
        raise ValueError(f"split must be one of {sorted(SPLIT_TEMPLATES)}")
    if equipment not in EQUIPMENT_ACCESS:
        raise ValueError(f"equipment must be one of {sorted(EQUIPMENT_ACCESS)}")
    if not isinstance(frequency, int) or not 2 <= frequency <= 6:
        raise ValueError("frequency must be an integer between 2 and 6")
    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("overrides must be a dict")
    if pattern_equipment is not None:
        if not isinstance(pattern_equipment, dict):
            raise ValueError("pattern_equipment must be a dict")
        for pattern, eq in pattern_equipment.items():
            if pattern not in PATTERNS:
                raise ValueError(f"unknown pattern in pattern_equipment: {pattern}")
            if eq not in EQUIPMENT_TAGS:
                raise ValueError(
                    f"pattern_equipment[{pattern}] must be one of {sorted(EQUIPMENT_TAGS)}"
                )
    if region_reps is not None:
        if not isinstance(region_reps, dict):
            raise ValueError("region_reps must be a dict")
        valid_choices = set(REP_RANGE_OPTIONS) | {"vary"}
        for region, choice in region_reps.items():
            if region not in REGIONS:
                raise ValueError(f"unknown region in region_reps: {region}")
            if choice not in valid_choices:
                raise ValueError(
                    f"region_reps[{region}] must be one of {sorted(valid_choices)}"
                )
    if frequency < SPLIT_MIN_FREQUENCY[split]:
        raise ValueError(
            f"{split} needs at least {SPLIT_MIN_FREQUENCY[split]} sessions/week; got {frequency}"
        )

    overrides = overrides or {}
    pattern_equipment = pattern_equipment or {}
    region_reps = region_reps or {}
    preferences = preferences or {}
    scheduling_style = preferences.get("scheduling_style", default_scheduling_style(experience))
    if scheduling_style not in ("stack", "stagger"):
        raise ValueError('scheduling_style must be "stack" or "stagger"')
    recovery = preferences.get("recovery", "average")
    if recovery not in RECOVERY_SET_ADJUSTMENT:
        raise ValueError(f"recovery must be one of {sorted(RECOVERY_SET_ADJUSTMENT)}")
    emphasis = preferences.get("emphasis", "balanced")
    if emphasis not in EMPHASIS_COMPOUND_REPS:
        raise ValueError(f"emphasis must be one of {sorted(EMPHASIS_COMPOUND_REPS)}")

    plan_warnings = set()
    if split == "full_body" and frequency > 4:
        plan_warnings.add(
            "Full-body 5-6x/week gives very little recovery between overlapping "
            "sessions — consider upper-lower or PPL at this frequency."
        )

    templates = SPLIT_TEMPLATES[split]
    positions, block_indices = phase_positions(running_plan)

    weeks = []
    session_cursor = 0  # split cycle continues across weeks
    for idx, running_week in enumerate(running_plan):
        engine_phase = running_week["phase"]
        strength_phase = PHASE_MAP.get(engine_phase)
        if strength_phase is None:
            raise ValueError(f"Unknown running phase: {engine_phase}")

        notes = []
        if strength_phase == "Race":
            weeks.append({
                "week": idx + 1,
                "phase": engine_phase,
                "strength_phase": "Race",
                "sessions": [],
                "warnings": [],
                "notes": ["Race week — no lifting. Show up fresh."],
            })
            continue

        week_templates = []
        for _ in range(frequency):
            week_templates.append(templates[session_cursor % len(templates)])
            session_cursor += 1

        assignments, warnings = place_sessions(
            running_week.get("schedule", {}), week_templates, scheduling_style
        )

        sessions = []
        for day, template in assignments:
            lifts = build_session_lifts(
                template, strength_phase, positions[idx], equipment,
                experience, recovery, emphasis, plan_warnings,
                rotation_index=block_indices[idx], overrides=overrides,
                pattern_equipment=pattern_equipment, region_reps=region_reps,
            )
            sessions.append({"day": day, "name": template["name"], "lifts": lifts})

        if strength_phase == "Deload":
            notes.append("Deload — reduced sets and effort. The taper is doing its job.")

        weeks.append({
            "week": idx + 1,
            "phase": engine_phase,
            "strength_phase": strength_phase,
            "sessions": sessions,
            "warnings": warnings,
            "notes": notes,
        })

    plan_notes = [PROGRESSION_NOTE]
    if scheduling_style == "stack":
        plan_notes.append(
            "Scheduling: hard days hard — strength stacks onto hard running days. "
            "Run first, lift second."
        )
    else:
        plan_notes.append(
            "Scheduling: staggered — strength sits on easy/rest days, kept off "
            "the day before hard runs."
        )
    plan_notes.extend(sorted(plan_warnings))

    return {"weeks": weeks, "notes": plan_notes}


# -----------------------------
# OUTPUT
# -----------------------------

def format_prescription(rx):
    if rx["rir"] is None:
        return f"{rx['name']} — {rx['sets']} × {rx['reps']}"
    return f"{rx['name']} — {rx['sets']} × {rx['reps']} @ {rx['rir']} RIR"


def print_strength_plan(strength_plan, show_cues=True):
    for note in strength_plan["notes"]:
        print(f"NOTE: {note}")
    print()
    for week in strength_plan["weeks"]:
        print(f"Week {week['week']} — {week['phase']} ({week['strength_phase']})")
        for note in week["notes"]:
            print(f"  {note}")
        for session in week["sessions"]:
            print(f"  {session['day']}: {session['name']}")
            for rx in session["lifts"]:
                print(f"    {format_prescription(rx)}")
                if show_cues:
                    print(f"      {rx['cue']}")
        for warning in week["warnings"]:
            print(f"  WARNING: {warning}")
        print()
