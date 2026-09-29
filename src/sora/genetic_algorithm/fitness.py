"""Fitness calculation for one daily chromosome."""

from dataclasses import dataclass

from sora.config import BASE_SLEEP_TARGET_SLOTS, GENES_PER_DAY, MAX_SLEEP_SLOTS, MIN_SLEEP_SLOTS, PENALTY_WEIGHTS
from sora.genetic_algorithm.constraints import ScheduleContext, is_nap_allowed_slot
from sora.genetic_algorithm.representation import Allele


@dataclass(frozen=True)
class FitnessResult:
    """Fitness output and supporting metrics."""

    fitness: float
    fatigue_end: float
    sleep_hours: float
    core_start: int
    recovery_reward: float
    dynamic_penalty: float
    regularity_penalty: float
    nap_sessions: int


def circadian_weight(slot: int) -> float:
    """Return recovery weight based on time of day."""
    if slot <= 12 or slot >= 44:
        return 1.20
    if 24 <= slot <= 32:
        return 0.85
    return 0.65


def _sleep_block_stats(chromosome: list[int], context: ScheduleContext) -> tuple[int, int]:
    sleep_blocks = 0
    current_len = 0
    max_len = 0
    longest_start = -1
    current_start = -1
    in_sleep = False
    for slot in range(GENES_PER_DAY):
        if chromosome[slot] == Allele.SLEEP:
            if not in_sleep:
                sleep_blocks += 1
                in_sleep = True
                current_start = slot
            current_len += 1
        else:
            if in_sleep and current_len > max_len:
                max_len = current_len
                longest_start = current_start
            in_sleep = False
            current_len = 0
    if in_sleep and current_len > max_len:
        longest_start = current_start

    if longest_start == 0 and context.tail_memory and context.tail_memory[-1] == Allele.SLEEP:
        sleep_blocks = max(1, sleep_blocks - 1)
    return sleep_blocks, longest_start


def calculate_fitness(chromosome: list[int], context: ScheduleContext) -> FitnessResult:
    """Calculate the complete SORA fitness score."""
    dynamic_penalty = 0.0
    actual_duration = chromosome.count(Allele.SLEEP)
    sleep_blocks, core_start = _sleep_block_stats(chromosome, context)

    if actual_duration == 0:
        dynamic_penalty -= PENALTY_WEIGHTS["DURATION"] * (24**2)

    free_slots = GENES_PER_DAY - len(context.mandatory_absolute)
    observed_target = len(context.observed_sleep_slots or [])
    target_sleep = min(
        observed_target or (BASE_SLEEP_TARGET_SLOTS + context.debt_installment),
        max(0, free_slots - 2),
    )

    if not context.survival_mode:
        if actual_duration < MIN_SLEEP_SLOTS:
            dynamic_penalty -= PENALTY_WEIGHTS["DURATION"] * ((MIN_SLEEP_SLOTS - actual_duration) ** 2)
        elif actual_duration > MAX_SLEEP_SLOTS:
            dynamic_penalty -= PENALTY_WEIGHTS["DURATION"] * ((actual_duration - MAX_SLEEP_SLOTS) ** 2)
        if actual_duration < target_sleep:
            dynamic_penalty -= PENALTY_WEIGHTS["DURATION"] * ((target_sleep - actual_duration) ** 2)
        if observed_target:
            duration_delta = abs(actual_duration - observed_target)
            dynamic_penalty -= 20.0 * (duration_delta**2)
            overlap = len({slot for slot, allele in enumerate(chromosome) if allele == Allele.SLEEP} & set(context.observed_sleep_slots))
            dynamic_penalty += overlap * 0.35
    elif chromosome.count(Allele.NAP) == 0:
        dynamic_penalty -= PENALTY_WEIGHTS["NAP_OVER"] * (3**2)

    max_blocks = 3 if not context.survival_mode else 4
    if sleep_blocks > max_blocks:
        dynamic_penalty -= PENALTY_WEIGHTS["BLOCK"] * ((sleep_blocks - max_blocks) ** 2)

    actual_naps = chromosome.count(Allele.NAP)
    if actual_naps > 3:
        dynamic_penalty -= PENALTY_WEIGHTS["NAP_OVER"] * ((actual_naps - 3) ** 2)

    nap_sessions = sum(
        1 for slot in range(GENES_PER_DAY) if chromosome[slot] == Allele.NAP and (slot == 0 or chromosome[slot - 1] != Allele.NAP)
    )
    if nap_sessions > 1:
        dynamic_penalty -= PENALTY_WEIGHTS["NAP_OVER"] * ((nap_sessions - 1) ** 2)

    regularity_penalty = 0.0
    if context.anchor_start is not None and context.anchor_start != -1 and core_start != -1:
        diff = min(abs(core_start - context.anchor_start), GENES_PER_DAY - abs(core_start - context.anchor_start))
        if diff > 4:
            anchor_blocked = any((context.anchor_start + offset) % GENES_PER_DAY in context.mandatory_absolute for offset in range(16))
            if not anchor_blocked:
                raw_penalty = PENALTY_WEIGHTS["REGULARITY"] * (diff - 4)
                regularity_penalty -= min(400.0, raw_penalty)

    current_fatigue = context.initial_fatigue
    recovery_reward = 0.0
    core_end_idx = -1
    for slot, allele in enumerate(chromosome):
        cw = circadian_weight(slot)
        if allele == Allele.WORK:
            current_fatigue += 0.08
        elif allele == Allele.CLASS:
            current_fatigue += 0.05
        elif allele == Allele.REST:
            current_fatigue += 0.03
        elif allele == Allele.NAP:
            if not is_nap_allowed_slot(slot):
                dynamic_penalty -= PENALTY_WEIGHTS["NAP_EARLY"]
                current_fatigue += 0.03
                current_fatigue = max(0, current_fatigue)
                continue
            if core_end_idx != -1 and (slot - core_end_idx) < 8:
                dynamic_penalty -= PENALTY_WEIGHTS["NAP_EARLY"]
            else:
                current_fatigue -= 0.35
                recovery_reward += 0.25 * cw
        elif allele == Allele.SLEEP:
            recovery_reward += current_fatigue * 0.15 * cw
            current_fatigue *= 1.0 - (0.15 * cw)
            core_end_idx = slot
        current_fatigue = max(0, current_fatigue)

    fitness = (context.sleep_weight * (recovery_reward + actual_duration * 0.2)) + dynamic_penalty + regularity_penalty
    return FitnessResult(
        fitness=float(fitness),
        fatigue_end=float(current_fatigue),
        sleep_hours=actual_duration / 2,
        core_start=int(core_start),
        recovery_reward=float(recovery_reward),
        dynamic_penalty=float(dynamic_penalty),
        regularity_penalty=float(regularity_penalty),
        nap_sessions=int(nap_sessions),
    )
