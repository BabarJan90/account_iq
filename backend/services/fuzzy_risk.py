"""
Fuzzy Logic + Explainable AI risk scoring engine.
This is the academic heart of the project — directly aligned with
Prof Hani Hagras's research in fuzzy logic and XAI.
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Tuple


class FuzzyRiskScorer:
    """
    Scores transaction risk using fuzzy logic rules.
    Produces a transparent, auditable risk score with a human-readable explanation.
    This mirrors what the KTP aims to build for ASP UK Ltd.
    """

    def __init__(self):
        self._build_fuzzy_system()

    def _build_fuzzy_system(self):
        # --- Input variables ---
        self.amount = ctrl.Antecedent(np.arange(0, 15001, 1), 'amount')
        self.vendor_trust = ctrl.Antecedent(np.arange(0, 11, 1), 'vendor_trust')
        self.frequency = ctrl.Antecedent(np.arange(0, 11, 1), 'frequency')

        # --- Output variable ---
        self.risk = ctrl.Consequent(np.arange(0, 101, 1), 'risk')

        # --- Membership functions for amount ---
        self.amount['low'] = fuzz.trimf(self.amount.universe, [0, 0, 500])
        self.amount['medium'] = fuzz.trimf(self.amount.universe, [300, 1500, 3000])
        self.amount['high'] = fuzz.trapmf(self.amount.universe, [2500, 5000, 15000, 15000])

        # --- Membership functions for vendor trust (10 = fully trusted) ---
        self.vendor_trust['untrusted'] = fuzz.trimf(self.vendor_trust.universe, [0, 0, 4])
        self.vendor_trust['neutral'] = fuzz.trimf(self.vendor_trust.universe, [3, 5, 7])
        self.vendor_trust['trusted'] = fuzz.trimf(self.vendor_trust.universe, [6, 10, 10])

        # --- Membership functions for transaction frequency (how often vendor appears) ---
        self.frequency['rare'] = fuzz.trimf(self.frequency.universe, [0, 0, 4])
        self.frequency['occasional'] = fuzz.trimf(self.frequency.universe, [3, 5, 7])
        self.frequency['frequent'] = fuzz.trimf(self.frequency.universe, [6, 10, 10])

        # --- Output membership functions ---
        self.risk['low'] = fuzz.trimf(self.risk.universe, [0, 0, 40])
        self.risk['medium'] = fuzz.trimf(self.risk.universe, [25, 50, 75])
        self.risk['high'] = fuzz.trapmf(self.risk.universe, [60, 80, 100, 100])

        # --- Fuzzy rules (transparent and auditable) ---
        rules = [
            ctrl.Rule(self.amount['high'] & self.vendor_trust['untrusted'], self.risk['high']),
            ctrl.Rule(self.amount['high'] & self.vendor_trust['neutral'], self.risk['medium']),
            ctrl.Rule(self.amount['high'] & self.vendor_trust['trusted'], self.risk['low']),
            ctrl.Rule(self.amount['medium'] & self.vendor_trust['untrusted'], self.risk['medium']),
            ctrl.Rule(self.amount['medium'] & self.vendor_trust['trusted'], self.risk['low']),
            ctrl.Rule(self.amount['low'] & self.vendor_trust['untrusted'] & self.frequency['rare'], self.risk['medium']),
            ctrl.Rule(self.amount['low'] & self.vendor_trust['trusted'], self.risk['low']),
            ctrl.Rule(self.frequency['rare'] & self.vendor_trust['untrusted'], self.risk['high']),
            ctrl.Rule(self.frequency['frequent'] & self.vendor_trust['trusted'], self.risk['low']),
        ]

        self.risk_ctrl = ctrl.ControlSystem(rules)
        self.risk_sim = ctrl.ControlSystemSimulation(self.risk_ctrl)

    def score(self, amount: float, vendor: str) -> Tuple[float, str, str]:
        """
        Returns (risk_score 0-100, risk_label, explanation).
        The explanation is the XAI component — human-readable reasoning.
        """
        vendor_trust_score = self._vendor_trust(vendor)
        frequency_score = self._vendor_frequency(vendor)

        try:
            self.risk_sim.input['amount'] = min(amount, 15000)
            self.risk_sim.input['vendor_trust'] = vendor_trust_score
            self.risk_sim.input['frequency'] = frequency_score
            self.risk_sim.compute()
            risk_score = float(self.risk_sim.output['risk'])
        except Exception:
            risk_score = 50.0

        risk_label = self._label(risk_score)
        explanation = self._explain(amount, vendor, vendor_trust_score, frequency_score, risk_score)

        return round(risk_score, 2), risk_label, explanation

    def _vendor_trust(self, vendor: str) -> float:
        """Assign a trust score based on vendor name heuristics."""
        trusted_keywords = ["HMRC", "Barclays", "Microsoft", "Amazon", "BT", "Vodafone",
                            "Adobe", "Slack", "Zoom", "Royal Mail", "DHL", "British Gas"]
        untrusted_keywords = ["Unknown", "Cash", "Wire", "International"]
        vendor_upper = vendor.upper()
        if any(k.upper() in vendor_upper for k in trusted_keywords):
            return 9.0
        if any(k.upper() in vendor_upper for k in untrusted_keywords):
            return 1.0
        return 5.0

    def _vendor_frequency(self, vendor: str) -> float:
        """In production this would query the DB. Here we use heuristics."""
        known_vendors = ["Amazon", "Microsoft", "Slack", "Zoom", "Adobe", "BT", "Vodafone"]
        if any(k in vendor for k in known_vendors):
            return 8.0
        if "Unknown" in vendor or "Cash" in vendor:
            return 1.0
        return 5.0

    def _label(self, score: float) -> str:
        if score < 35:
            return "low"
        elif score < 65:
            return "medium"
        return "high"

    def _explain(self, amount: float, vendor: str, trust: float,
                 frequency: float, score: float) -> str:
        """
        XAI: Generate a transparent, plain-English explanation of the risk decision.
        This is what accountants and auditors can read to understand the AI's reasoning.
        """
        parts = []

        if amount > 5000:
            parts.append(f"the transaction amount of £{amount:,.2f} is unusually high")
        elif amount > 1500:
            parts.append(f"the transaction amount of £{amount:,.2f} is above average")
        else:
            parts.append(f"the transaction amount of £{amount:,.2f} is within normal range")

        if trust <= 3:
            parts.append(f"'{vendor}' is an unrecognised or untrusted vendor")
        elif trust >= 7:
            parts.append(f"'{vendor}' is a well-known, trusted vendor")
        else:
            parts.append(f"'{vendor}' has a neutral trust profile")

        if frequency <= 3:
            parts.append("this vendor appears infrequently in the accounts")

        label = self._label(score)
        reasoning = ", ".join(parts)
        return (f"Risk assessed as {label.upper()} (score: {score:.0f}/100). "
                f"Contributing factors: {reasoning}.")


# Singleton instance
fuzzy_scorer = FuzzyRiskScorer()
