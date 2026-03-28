"""Seed the database with realistic mock accounting transactions."""
from db.database import SessionLocal, Transaction, init_db
from datetime import datetime, timedelta
import random

VENDORS = [
    "Amazon Web Services", "Microsoft Azure", "Office Supplies Ltd",
    "British Gas", "Royal Mail", "HMRC", "Barclays Bank",
    "Unknown Vendor 1234", "Cash Withdrawal", "International Wire XYZ",
    "Slack Technologies", "Zoom Communications", "Adobe Systems",
    "BT Business", "Vodafone UK", "Staples UK", "DHL Express"
]

CATEGORIES = ["Software", "Utilities", "Supplies", "Tax", "Banking",
               "Communications", "Shipping", "Unknown"]

NORMAL_AMOUNTS = [29.99, 49.00, 120.00, 250.00, 89.99, 199.00, 45.50]
SUSPICIOUS_AMOUNTS = [9850.00, 4999.99, 12000.00, 7500.00]


def seed_transactions(n: int = 50):
    init_db()
    db = SessionLocal()

    try:
        existing = db.query(Transaction).count()
        if existing > 0:
            print(f"Database already has {existing} transactions. Skipping seed.")
            return

        transactions = []
        base_date = datetime.now() - timedelta(days=90)

        for i in range(n):
            is_suspicious = random.random() < 0.15   # 15% suspicious
            vendor = random.choice(VENDORS)
            amount = random.choice(SUSPICIOUS_AMOUNTS) if is_suspicious \
                else random.choice(NORMAL_AMOUNTS) * random.uniform(0.8, 3.0)
            category = "Unknown" if "Unknown" in vendor or "Cash" in vendor or "Wire" in vendor \
                else random.choice(CATEGORIES)

            t = Transaction(
                date=str(base_date + timedelta(days=random.randint(0, 90))),
                vendor=vendor,
                amount=round(amount, 2),
                category=category,
                description=f"Transaction ref TXN{1000 + i}",
            )
            transactions.append(t)

        db.add_all(transactions)
        db.commit()
        print(f"Seeded {n} transactions successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_transactions()
