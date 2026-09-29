"""Chromosome repair procedures after initialization, crossover, and mutation."""

from sora.config import BASE_SLEEP_TARGET_SLOTS, GENES_PER_DAY
from sora.genetic_algorithm.constraints import ScheduleContext, is_nap_allowed_slot
from sora.genetic_algorithm.representation import Allele, validate_chromosome


def enforce_mandatory_slots(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Force work, class, and transit slots back to their required values."""
    for slot in range(GENES_PER_DAY):
        if slot in context.work_slots:
            chromosome[slot] = Allele.WORK
        elif slot in context.class_slots:
            chromosome[slot] = Allele.CLASS
        elif slot in context.transit_slots:
            chromosome[slot] = Allele.REST
    return chromosome


def remove_micro_sleeps(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Remove sleep fragments shorter than 3 slots, except midnight continuity."""
    in_sleep = False
    start_idx = -1
    length = 0
    for slot in range(GENES_PER_DAY + 1):
        current = chromosome[slot] if slot < GENES_PER_DAY else -1
        if current == Allele.SLEEP:
            if not in_sleep:
                in_sleep = True
                start_idx = slot
            length += 1
        elif in_sleep:
            if length < 3:
                destroy = True
                if start_idx == 0 and context.tail_memory and context.tail_memory[-1] == Allele.SLEEP:
                    destroy = False
                if start_idx + length == GENES_PER_DAY:
                    destroy = False
                if destroy:
                    for offset in range(length):
                        target = start_idx + offset
                        if target not in context.mandatory_absolute:
                            chromosome[target] = Allele.REST
            in_sleep = False
            length = 0
    return chromosome


def sanitize_transitions(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Avoid direct nap-sleep transitions that blur nap and main sleep."""
    if context.tail_memory and context.tail_memory[-1] == Allele.SLEEP and chromosome[0] == Allele.NAP:
        for slot in range(GENES_PER_DAY):
            if chromosome[slot] == Allele.NAP and slot not in context.mandatory_absolute:
                chromosome[slot] = Allele.SLEEP
            else:
                break

    for slot in range(GENES_PER_DAY):
        if chromosome[slot] != Allele.NAP:
            continue
        adjacent_to_sleep = (
            (slot > 0 and chromosome[slot - 1] == Allele.SLEEP)
            or (slot < GENES_PER_DAY - 1 and chromosome[slot + 1] == Allele.SLEEP)
        )
        if adjacent_to_sleep and slot not in context.mandatory_absolute:
            chromosome[slot] = Allele.SLEEP
    return chromosome


def enforce_sleep_target(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Expand sleep blocks toward the target using free rest slots."""
    if chromosome.count(Allele.SLEEP) == 0:
        for slot in range(GENES_PER_DAY):
            if chromosome[slot] == Allele.REST and slot not in context.mandatory_absolute:
                chromosome[slot] = Allele.SLEEP
                break

    free_slots = GENES_PER_DAY - len(context.mandatory_absolute)
    target_sleep = min(
        len(context.observed_sleep_slots or []) or (BASE_SLEEP_TARGET_SLOTS + context.debt_installment),
        max(0, free_slots - 2),
    )

    while chromosome.count(Allele.SLEEP) < target_sleep:
        changed = False
        for slot in range(GENES_PER_DAY):
            if chromosome[slot] != Allele.SLEEP:
                continue
            previous_slot = slot - 1
            next_slot = slot + 1
            if (
                previous_slot >= 0
                and chromosome[previous_slot] == Allele.REST
                and previous_slot not in context.mandatory_absolute
            ):
                chromosome[previous_slot] = Allele.SLEEP
                changed = True
            if (
                next_slot < GENES_PER_DAY
                and chromosome[next_slot] == Allele.REST
                and next_slot not in context.mandatory_absolute
            ):
                chromosome[next_slot] = Allele.SLEEP
                changed = True
        if not changed:
            break
    return chromosome


def bridge_gaps(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Bridge small rest gaps between sleep or nap fragments."""
    in_gap = False
    gap_start = -1
    target_gene = -1
    for slot in range(GENES_PER_DAY):
        if chromosome[slot] == Allele.REST and slot not in context.mandatory_absolute:
            if not in_gap:
                left_anchor = (
                    (slot > 0 and chromosome[slot - 1] in [Allele.SLEEP, Allele.NAP])
                    or (slot == 0 and context.tail_memory and context.tail_memory[-1] in [Allele.SLEEP, Allele.NAP])
                )
                if left_anchor:
                    in_gap = True
                    gap_start = slot
                    target_gene = chromosome[slot - 1] if slot > 0 else context.tail_memory[-1]
        elif chromosome[slot] == target_gene:
            if in_gap:
                gap_len = slot - gap_start
                if target_gene == Allele.SLEEP and gap_len <= 6:
                    for target in range(gap_start, slot):
                        chromosome[target] = Allele.SLEEP
                elif target_gene == Allele.NAP and gap_len <= 2:
                    for target in range(gap_start, slot):
                        chromosome[target] = Allele.NAP
            in_gap = False
        else:
            in_gap = False
    return chromosome


def limit_nap_duration(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Allow nap only inside the nap window and limit it to 3 slots."""
    nap_len = 0
    for slot in range(GENES_PER_DAY):
        if chromosome[slot] == Allele.NAP and not is_nap_allowed_slot(slot) and slot not in context.mandatory_absolute:
            chromosome[slot] = Allele.REST
            nap_len = 0
        elif chromosome[slot] == Allele.NAP:
            nap_len += 1
            if nap_len > 3 and slot not in context.mandatory_absolute:
                chromosome[slot] = Allele.REST
        else:
            nap_len = 0
    return chromosome


def repair_chromosome(chromosome: list[int], context: ScheduleContext) -> list[int]:
    """Run all repair procedures in dependency-safe order."""
    validate_chromosome(chromosome)
    chromosome = enforce_mandatory_slots(chromosome, context)
    chromosome = remove_micro_sleeps(chromosome, context)
    chromosome = sanitize_transitions(chromosome, context)
    chromosome = enforce_sleep_target(chromosome, context)
    chromosome = bridge_gaps(chromosome, context)
    chromosome = limit_nap_duration(chromosome, context)
    chromosome = enforce_mandatory_slots(chromosome, context)
    validate_chromosome(chromosome)
    return chromosome