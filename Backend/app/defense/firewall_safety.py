
from app.defense.recommendation_rules import RecommendedAction


class FirewallSafetyError(Exception):
    """Raised when a real firewall action is requested."""


class FirewallSafetyGuard:
    """
    Restricts response actions to simulation-only recommendations.

    No actual firewall execution is implemented here.
    """

    ALLOWED_ACTIONS = frozenset(
        {
            RecommendedAction.MONITOR,
            RecommendedAction.INVESTIGATE,
            RecommendedAction.SIMULATED_BLOCK,
        }
    )

    @classmethod
    def validate_action(cls, action: RecommendedAction) -> None:
        if (
            not isinstance(action, RecommendedAction)
            or action not in cls.ALLOWED_ACTIONS
        ):
            raise FirewallSafetyError(
                "Real or unsupported security actions are forbidden."
            )
