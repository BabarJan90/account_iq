"""
NLP service — entity extraction from financial transaction descriptions.
Uses spaCy for named entity recognition and custom financial pattern matching.
"""
import re
from typing import Dict, List


class NLPService:
    """
    Extracts structured information from unstructured financial text.
    In production this would use a fine-tuned spaCy model on accounting data.
    For the demo we use rule-based extraction + regex patterns.
    """

    CURRENCY_PATTERN = re.compile(r'£([\d,]+\.?\d*)')
    DATE_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')
    REF_PATTERN = re.compile(r'TXN\d+|INV-\d+|REF-\w+', re.IGNORECASE)

    FINANCIAL_KEYWORDS = {
        "invoice": ["invoice", "inv", "bill"],
        "payment": ["payment", "paid", "transfer", "wire"],
        "refund": ["refund", "credit", "return"],
        "salary": ["salary", "payroll", "wages"],
        "tax": ["vat", "hmrc", "tax", "paye"],
        "subscription": ["subscription", "monthly", "annual", "renewal"],
    }

    def extract_entities(self, text: str) -> Dict:
        """Extract key entities from a transaction description."""
        text_lower = text.lower()
        entities = {
            "references": self.REF_PATTERN.findall(text),
            "amounts": self.CURRENCY_PATTERN.findall(text),
            "dates": self.DATE_PATTERN.findall(text),
            "transaction_types": [],
            "flags": [],
        }

        for tx_type, keywords in self.FINANCIAL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                entities["transaction_types"].append(tx_type)

        # Flag suspicious patterns
        if any(word in text_lower for word in ["international", "wire", "offshore"]):
            entities["flags"].append("international_transfer")
        if any(word in text_lower for word in ["cash", "atm", "withdrawal"]):
            entities["flags"].append("cash_transaction")
        if re.search(r'£[4-9]\d{3}', text):
            entities["flags"].append("near_reporting_threshold")

        return entities

    def classify_transaction(self, vendor: str, description: str, amount: float) -> str:
        """Auto-classify a transaction into a category."""
        text = f"{vendor} {description}".lower()

        rules = [
            (["hmrc", "vat", "paye", "tax"], "Tax & Compliance"),
            (["salary", "payroll", "wages", "hr"], "Payroll"),
            (["aws", "azure", "google cloud", "hosting", "saas"], "Software & Cloud"),
            (["office", "supplies", "stationery", "staples"], "Office Supplies"),
            (["gas", "electricity", "water", "utilities", "bt ", "vodafone"], "Utilities"),
            (["royal mail", "dhl", "fedex", "courier", "shipping"], "Logistics"),
            (["barclays", "lloyds", "hsbc", "bank", "natwest"], "Banking"),
            (["slack", "zoom", "teams", "microsoft", "adobe"], "Software"),
        ]

        for keywords, category in rules:
            if any(kw in text for kw in keywords):
                return category

        if amount > 5000:
            return "High-Value — Review Required"

        return "Uncategorised"

    def summarise_transactions(self, transactions: List[Dict]) -> str:
        """Generate a plain-English summary of a batch of transactions."""
        if not transactions:
            return "No transactions to summarise."

        total = sum(t.get("amount", 0) for t in transactions)
        high_risk = [t for t in transactions if t.get("risk_label") == "high"]
        categories = {}
        for t in transactions:
            cat = t.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + t.get("amount", 0)

        top_category = max(categories, key=categories.get) if categories else "Unknown"
        summary = (
            f"Analysed {len(transactions)} transactions totalling £{total:,.2f}. "
            f"Highest spending category: {top_category} "
            f"(£{categories.get(top_category, 0):,.2f}). "
        )
        if high_risk:
            summary += (f"{len(high_risk)} transaction(s) flagged as HIGH RISK "
                        f"requiring immediate review.")
        else:
            summary += "No high-risk transactions detected."

        return summary


nlp_service = NLPService()
