from scheduler_simulator.scheduler_base import SchedulerBase

from .round_robin import RoundRobinScheduler, create_round_robin_from_config
from .hadqrr import HADQRRScheduler, create_hadqrr_from_config
from .enhanced_rr import EnhancedRR, create_err_scheduler_from_config
from .proposed_1 import ProposedScheduler_1, create_proposed_scheduler_1_from_config
from .proposed_2 import ProposedScheduler_2, create_proposed_scheduler_2_from_config


def create_scheduler_from_config(config: dict) -> 'SchedulerBase':
    if not isinstance(config, dict):
        raise ValueError("Each scheduler must be a JSON object.")
    unknown = set(config) - {"name", "type", "parameters"}
    if unknown:
        raise ValueError(f"Unknown scheduler fields: {sorted(unknown)}")
    scheduler_type = config.get("type")
    if not isinstance(scheduler_type, str) or not scheduler_type.strip():
        raise ValueError("Scheduler type must be a non-empty string.")
    factories = {
        "round_robin": (create_round_robin_from_config, {"time_quantum"}),
        "hadqrr": (create_hadqrr_from_config, {"default_time_quantum", "history_length"}),
        "enhanced_rr": (create_err_scheduler_from_config, set()),
        "proposed_1": (create_proposed_scheduler_1_from_config, {"default_time_quantum", "alpha"}),
        "proposed_2": (create_proposed_scheduler_2_from_config, {"default_time_quantum", "alpha", "aging_factor"}),

    }
    scheduler_type = scheduler_type.lower()
    if scheduler_type not in factories:
        raise ValueError(f"Unknown scheduler type: {scheduler_type}")
    factory, allowed = factories[scheduler_type]
    parameters = config.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("Scheduler parameters must be a JSON object.")
    if set(parameters) - allowed:
        raise ValueError(f"Unknown parameters for {scheduler_type}: {sorted(set(parameters) - allowed)}")
    if "name" in config and (not isinstance(config["name"], str) or not config["name"].strip()):
        raise ValueError("Scheduler name must be a non-empty string.")
    return factory(parameters)
