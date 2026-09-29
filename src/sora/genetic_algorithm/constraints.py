"""Schedule constraints used by the Genetic Algorithm."""

from dataclasses import dataclass

from sora.config import GENES_PER_DAY, NAP_ALLOWED_END, NAP_ALLOWED_START


@dataclass
class ScheduleContext:
    """Immutable-ish context for one daily optimization problem."""

    work_slots: list[int]
    class_slots: list[int]
    population_size: int
    mutation_rate: float
    crossover_rate: float
    observed_sleep_slots: list[int] | None = None
    sleep_weight: float = 0.65
    initial_fatigue: float = 0.0
    anchor_start: int | None = None
    debt_installment: int = 0
    tail_memory: list[int] | None = None

    def __post_init__(self) -> None:
        _validate_slots("work_slots", self.work_slots)
        _validate_slots("class_slots", self.class_slots)
        _validate_slots("observed_sleep_slots", self.observed_sleep_slots or [])
        overlap = sorted(set(self.work_slots) & set(self.class_slots))
        if overlap:
            raise ValueError(f"work_slots and class_slots overlap: {overlap}")
        if self.population_size < 2:
            raise ValueError("population_size must be at least 2")
        if not 0 < self.mutation_rate <= 1:
            raise ValueError("mutation_rate must be in range (0, 1]")
        if not 0 <= self.crossover_rate <= 1:
            raise ValueError("crossover_rate must be in range [0, 1]")
        if self.tail_memory is not None:
            _validate_tail_memory(self.tail_memory)

        self.mandatory_core = sorted(set(self.work_slots + self.class_slots))
        self.transit_slots = build_transit_slots(self.mandatory_core)
        self.mandatory_absolute = sorted(set(self.mandatory_core + self.transit_slots))
        self.survival_mode = is_survival_mode(self.mandatory_absolute)


def _validate_slots(field_name: str, slots: list[int]) -> None:
    """Validate slot collections accepted by the public optimizer API."""
    if not isinstance(slots, list):
        raise TypeError(f"{field_name} must be a list")
    if not all(type(slot) is int and 0 <= slot < GENES_PER_DAY for slot in slots):
        raise ValueError(f"{field_name} must contain integers in range 0-47")
    if len(slots) != len(set(slots)):
        raise ValueError(f"{field_name} contains duplicate slots")


def _validate_tail_memory(tail_memory: list[int]) -> None:
    """Validate previous-day memory used for midnight sleep continuity."""
    if not isinstance(tail_memory, list):
        raise TypeError("tail_memory must be a list")
    if len(tail_memory) > GENES_PER_DAY:
        raise ValueError(f"tail_memory cannot exceed {GENES_PER_DAY} genes")
    if not all(isinstance(allele, int) and type(allele) is not bool and 0 <= allele <= 4 for allele in tail_memory):
        raise ValueError("tail_memory must contain allele integers in range 0-4")


def build_transit_slots(mandatory_core: list[int]) -> list[int]:
    """Add one rest slot before and after mandatory work/class slots."""
    transit_slots = []
    mandatory_set = set(mandatory_core)
    for slot in mandatory_core:
        if slot > 0 and (slot - 1) not in mandatory_set:
            transit_slots.append(slot - 1)
        if slot < GENES_PER_DAY - 1 and (slot + 1) not in mandatory_set:
            transit_slots.append(slot + 1)
    return sorted(set(transit_slots))


def is_nap_allowed_slot(slot: int) -> bool:
    """Return True if slot is inside the academic nap window."""
    return NAP_ALLOWED_START <= slot < NAP_ALLOWED_END


def check_feasibility(mandatory_absolute: list[int]) -> bool:
    """Reject days where mandatory slots leave no room for minimum sleep."""
    return len(mandatory_absolute) <= 36


def is_survival_mode(mandatory_absolute: list[int]) -> bool:
    """Detect dense schedules without a continuous 6-hour free block."""
    max_streak = 0
    current_streak = 0
    mandatory = set(mandatory_absolute)
    for slot in range(GENES_PER_DAY):
        if slot not in mandatory:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak < 12 and bool(mandatory_absolute)
