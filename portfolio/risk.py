"""
Risk Engine — deterministic risk level adjustment based on sentiment scores.
"""

from config.config import (
    RISK_ALLOCATIONS,
    STRONG_BULLISH_THRESHOLD,
    STRONG_BEARISH_THRESHOLD,
)


class RiskEngine:
    """
    Deterministic, rule-based risk level adjustment.
    Maps sentiment scores to risk levels and target allocations.
    """

    def __init__(self):
        self.allocations = RISK_ALLOCATIONS

    def determine_risk_level(self, sentiment_score: float, current_risk: str) -> dict:
        """
        Determine the new risk level based on sentiment score.
        
        Rules (deterministic):
            score > +0.5  → High risk (aggressive, more equity)
            score -0.3 to +0.5 → Medium risk (balanced)
            score < -0.3 → Low risk (defensive, more cash/bonds)
        
        Args:
            sentiment_score: Aggregate sentiment score (-1.0 to +1.0)
            current_risk: Current risk level ('Low', 'Medium', 'High')
        
        Returns:
            Dict with new risk level, adjustment description, and target allocation
        """
        # Determine new risk level
        if sentiment_score > STRONG_BULLISH_THRESHOLD:
            new_risk = "High"
        elif sentiment_score < STRONG_BEARISH_THRESHOLD:
            new_risk = "Low"
        else:
            new_risk = "Medium"

        # Determine if risk changed
        if new_risk == current_risk:
            adjustment = f"Maintain {current_risk} risk — sentiment supports current allocation"
        else:
            adjustment = f"{current_risk} → {new_risk}"

        target = self.allocations[new_risk]

        return {
            "previous_risk": current_risk,
            "new_risk": new_risk,
            "risk_changed": new_risk != current_risk,
            "adjustment": adjustment,
            "target_allocation": target,
            "sentiment_score": sentiment_score,
        }

    def get_rebalance_actions(
        self, current_allocation: dict, target_allocation: dict
    ) -> dict:
        """
        Compare current allocation vs target and determine what needs to change.
        
        Args:
            current_allocation: Dict with equity_pct, bonds_pct, cash_pct
            target_allocation: Dict with equity, bonds, cash target percentages
        
        Returns:
            Dict describing needed allocation shifts
        """
        equity_diff = target_allocation["equity"] - current_allocation.get("equity_pct", 50)
        bonds_diff = target_allocation["bonds"] - current_allocation.get("bonds_pct", 30)
        cash_diff = target_allocation["cash"] - current_allocation.get("cash_pct", 20)

        actions = []
        if equity_diff > 2:
            actions.append(f"Increase equity by {equity_diff:.1f}%")
        elif equity_diff < -2:
            actions.append(f"Decrease equity by {abs(equity_diff):.1f}%")

        if bonds_diff > 2:
            actions.append(f"Increase bonds by {bonds_diff:.1f}%")
        elif bonds_diff < -2:
            actions.append(f"Decrease bonds by {abs(bonds_diff):.1f}%")

        if cash_diff > 2:
            actions.append(f"Increase cash by {cash_diff:.1f}%")
        elif cash_diff < -2:
            actions.append(f"Decrease cash by {abs(cash_diff):.1f}%")

        if not actions:
            actions.append("Portfolio is within target allocation — no rebalancing needed")

        return {
            "equity_diff": round(equity_diff, 2),
            "bonds_diff": round(bonds_diff, 2),
            "cash_diff": round(cash_diff, 2),
            "actions": actions,
        }
