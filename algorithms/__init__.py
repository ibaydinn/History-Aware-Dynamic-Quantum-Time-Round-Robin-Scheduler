from scheduler_simulator.scheduler_base import SchedulerBase

from .round_robin import RoundRobinScheduler, create_round_robin_from_config
from .hadqrr import HADQRRScheduler, create_hadqrr_from_config
from .enhanced_rr import EnhancedRR, create_err_scheduler_from_config


def create_scheduler_from_config(config: dict) -> 'SchedulerBase':
    scheduler_type = config.get("type")
    if not scheduler_type:
        raise ValueError("Scheduler type must be specified in the configuration.")

    scheduler_type = scheduler_type.lower()
    
    if scheduler_type == "round_robin":
        return create_round_robin_from_config(config)
    elif scheduler_type == "hadqrr":
        return create_hadqrr_from_config(config)
    elif scheduler_type == "enhanced_rr":
        return create_err_scheduler_from_config(config)
    else:
        raise ValueError(f"Unknown scheduler type: {scheduler_type}")