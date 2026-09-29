"""Global constants for the SORA academic implementation."""

GENES_PER_DAY = 48
SLOT_DURATION_HOURS = 0.5
DEFAULT_RANDOM_SEED = 42

DEFAULT_POPULATION_SIZE = 50
DEFAULT_MUTATION_RATE = 0.10
DEFAULT_CROSSOVER_RATE = 0.80

DATASET_CALIBRATION = "dataset/dataset_kalibrasi_sora.csv"
DATASET_TEST = "dataset/kuisoner (Jawaban) - Form Responses 1.csv"
PARAMETER_FILE = "results/best_params_academic.json"
HISTORY_FILE = "results/sleep_history.csv"
THESIS_OUTPUT_DIR = "thesis_output_academic"

BASE_SLEEP_TARGET_SLOTS = 14
MIN_SLEEP_SLOTS = 12
MAX_SLEEP_SLOTS = 18

NAP_ALLOWED_START = 24
NAP_ALLOWED_END = 34

PENALTY_WEIGHTS = {
    "BLOCK": 300.0,
    "DURATION": 200.0,
    "NAP_EARLY": 150.0,
    "NAP_OVER": 150.0,
    "REGULARITY": 100.0,
}
