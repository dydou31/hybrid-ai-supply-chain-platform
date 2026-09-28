import re
from collections import Counter, defaultdict
from decimal import Decimal

from app.database import SessionLocal
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


def _normalize_question(question: str) -> str:
    text = question.lower()

    replacements = {
        "frns": "fournisseur",
        "fourn": "fournisseur",
        "supplier": "fournisseur",
        "suppliers": "fournisseur",
        "po": "commande",
        "cde": "commande",
        "cmd": "commande",
    }

    for source, target in replacements.items():
        text = re.sub(
            rf"\b{re.escape(source)}\b",
            target,
            text,
        )

    return text


def get_relevant_structured_context(question: str) -> str:
    db = SessionLocal()

    try:
        q = _normalize_question(question)

        suppliers = db.query(Supplier).all()
        purchase_orders = db.query(PurchaseOrder).all()

        total_suppliers = len(suppliers)

        risk_counts = Counter(
            supplier.risk_level
            for supplier in suppliers
        )

        total_blocked_stock = sum(
            (
                supplier.blocked_stock_eur
                or Decimal("0")
                for supplier in suppliers
            ),
            Decimal("0"),
        )

        highest_blocked = max(
            suppliers,
            key=lambda supplier:
                supplier.blocked_stock_eur or Decimal("0"),
            default=None,
        )

        # ----- Purchase Order KPIs -----

        orders_by_supplier = defaultdict(list)

        for po in purchase_orders:
            orders_by_supplier[po.supplier_id].append(po)

        delayed_by_supplier = {}

        for supplier in suppliers:
            orders = orders_by_supplier.get(supplier.id, [])

            delayed = [
                po
                for po in orders
                if po.confirmed_date
                and po.requested_date
                and po.confirmed_date > po.requested_date
            ]

            delayed_by_supplier[supplier.id] = delayed

        total_delayed_orders = sum(
            len(delayed)
            for delayed in delayed_by_supplier.values()
        )

        supplier_with_most_delays = max(
            suppliers,
            key=lambda supplier:
                len(delayed_by_supplier.get(supplier.id, [])),
            default=None,
        )

        lines = [
            "RELEVANT STRUCTURED DATA",
        ]

        # Total delayed purchase orders
        if (
            "combien" in q
            and "commande" in q
            and (
                "retard" in q
                or "late" in q
                or "delay" in q
            )
        ):
            lines.append(
                f"Total delayed purchase orders: "
                f"{total_delayed_orders}"
            )
            return "\n".join(lines)

        # ----- Ranked supplier analysis -----

        def supplier_metrics(supplier):
            orders = orders_by_supplier.get(supplier.id, [])
            delayed = delayed_by_supplier.get(supplier.id, [])

            delay_rate = (
                len(delayed) / len(orders) * 100
                if orders
                else 0
            )

            delay_days = [
                (po.confirmed_date - po.requested_date).days
                for po in delayed
            ]

            average_delay = (
                sum(delay_days) / len(delay_days)
                if delay_days
                else 0
            )

            return {
                "supplier": supplier,
                "orders": len(orders),
                "delayed": len(delayed),
                "delay_rate": delay_rate,
                "average_delay": average_delay,
                "blocked_stock": (
                    supplier.blocked_stock_eur
                    or Decimal("0")
                ),
            }

        metrics = [
            supplier_metrics(supplier)
            for supplier in suppliers
        ]

        # Best supplier according to available operational KPIs
        if (
            "fournisseur" in q
            and any(
                term in q
                for term in ("meilleur", "meilleure", "best")
            )
        ):
            risk_rank = {
                "low": 0,
                "medium": 1,
                "high": 2,
            }

            candidates = [
                item
                for item in metrics
                if item["orders"] > 0
            ]

            if candidates:
                best = min(
                    candidates,
                    key=lambda item: (
                        risk_rank.get(
                            item["supplier"].risk_level,
                            99,
                        ),
                        item["delay_rate"],
                        item["average_delay"],
                        item["blocked_stock"],
                    ),
                )

                supplier = best["supplier"]
                on_time_rate = 100 - best["delay_rate"]

                lines.append(
                    "Best supplier according to available operational KPIs:"
                )
                lines.append(f"Supplier: {supplier.name}")
                lines.append(f"Risk level: {supplier.risk_level}")
                lines.append(
                    f"On-time delivery rate: {on_time_rate:.2f}%"
                )
                lines.append(
                    f"Delayed purchase orders: "
                    f"{best['delayed']}/{best['orders']}"
                )
                lines.append(
                    f"Average delay days: "
                    f"{best['average_delay']:.2f}"
                )
                lines.append(
                    f"Blocked stock EUR: "
                    f"{best['blocked_stock']}"
                )
                lines.append(
                    "Ranking criteria, in order: risk level, "
                    "delay rate, average delay, blocked stock."
                )

                return "\n".join(lines)

        # Multicriteria analysis:
        # high risk + delays + blocked stock
        if (
            "fournisseur" in q
            and (
                "cumul" in q
                or "combine" in q
                or "combin" in q
            )
            and "risqu" in q
            and "retard" in q
            and "stock" in q
        ):
            candidates = [
                item
                for item in metrics
                if item["supplier"].risk_level == "high"
                and item["delayed"] > 0
            ]

            candidates.sort(
                key=lambda item: (
                    item["delayed"],
                    item["delay_rate"],
                    item["blocked_stock"],
                ),
                reverse=True,
            )

            lines.append(
                "Ranking criteria: high risk suppliers only; "
                "then delayed orders, delay rate, blocked stock."
            )

            for rank, item in enumerate(
                candidates[:5],
                start=1,
            ):
                supplier = item["supplier"]

                lines.append(
                    f"{rank}. {supplier.name} | "
                    f"risk={supplier.risk_level} | "
                    f"delayed={item['delayed']}/{item['orders']} | "
                    f"delay_rate={item['delay_rate']:.2f}% | "
                    f"avg_delay_days={item['average_delay']:.2f} | "
                    f"blocked_stock_eur={item['blocked_stock']}"
                )

            return "\n".join(lines)

        # High-risk suppliers ranked by delayed orders
        if (
            "fournisseur" in q
            and "high" in q
            and "retard" in q
            and any(
                term in q
                for term in ("plus", "top", "most")
            )
        ):
            candidates = [
                item
                for item in metrics
                if item["supplier"].risk_level == "high"
            ]

            candidates.sort(
                key=lambda item: (
                    item["delayed"],
                    item["delay_rate"],
                    item["blocked_stock"],
                ),
                reverse=True,
            )

            lines.append(
                "High risk suppliers ranked by delayed orders:"
            )

            for rank, item in enumerate(
                candidates[:5],
                start=1,
            ):
                supplier = item["supplier"]

                lines.append(
                    f"{rank}. {supplier.name} | "
                    f"delayed={item['delayed']}/{item['orders']} | "
                    f"delay_rate={item['delay_rate']:.2f}% | "
                    f"avg_delay_days={item['average_delay']:.2f} | "
                    f"blocked_stock_eur={item['blocked_stock']}"
                )

            return "\n".join(lines)

        # Top suppliers by delayed orders
        if (
            "fournisseur" in q
            and "retard" in q
            and any(
                term in q
                for term in ("top", "5", "cinq")
            )
        ):
            ranked = sorted(
                metrics,
                key=lambda item: (
                    item["delayed"],
                    item["delay_rate"],
                    item["blocked_stock"],
                ),
                reverse=True,
            )

            lines.append(
                "Top 5 suppliers by delayed purchase orders:"
            )

            for rank, item in enumerate(
                ranked[:5],
                start=1,
            ):
                supplier = item["supplier"]

                lines.append(
                    f"{rank}. {supplier.name} | "
                    f"delayed={item['delayed']}/{item['orders']} | "
                    f"delay_rate={item['delay_rate']:.2f}% | "
                    f"avg_delay_days={item['average_delay']:.2f} | "
                    f"blocked_stock_eur={item['blocked_stock']}"
                )

            return "\n".join(lines)

        # Supplier with most delayed orders
        if (
            "fournisseur" in q
            and (
                "retard" in q
                or "late" in q
                or "delay" in q
            )
            and any(
                term in q
                for term in (
                    "plus",
                    "maximum",
                    "max",
                    "most",
                )
            )
            and supplier_with_most_delays
        ):
            delayed = delayed_by_supplier.get(
                supplier_with_most_delays.id,
                [],
            )

            orders = orders_by_supplier.get(
                supplier_with_most_delays.id,
                [],
            )

            delay_rate = (
                len(delayed) / len(orders) * 100
                if orders
                else 0
            )

            delay_days = [
                (
                    po.confirmed_date
                    - po.requested_date
                ).days
                for po in delayed
            ]

            average_delay = (
                sum(delay_days) / len(delay_days)
                if delay_days
                else 0
            )

            lines.extend(
                [
                    (
                        "Supplier with most delayed orders: "
                        f"{supplier_with_most_delays.name}"
                    ),
                    (
                        "Delayed purchase orders: "
                        f"{len(delayed)}"
                    ),
                    (
                        "Total purchase orders: "
                        f"{len(orders)}"
                    ),
                    f"Delay rate: {delay_rate:.2f}%",
                    (
                        "Average delay days: "
                        f"{average_delay:.2f}"
                    ),
                ]
            )

            return "\n".join(lines)

        # Supplier count
        if (
            "combien" in q
            and "fournisseur" in q
            and not any(
                risk in q
                for risk in ("high", "medium", "low")
            )
        ):
            lines.append(
                f"Total suppliers: {total_suppliers}"
            )
            return "\n".join(lines)

        # Supplier count by risk
        for risk in ("high", "medium", "low"):
            if (
                risk in q
                and "fournisseur" in q
                and "combien" in q
            ):
                lines.append(
                    f"{risk.capitalize()} risk suppliers: "
                    f"{risk_counts.get(risk, 0)}"
                )
                return "\n".join(lines)

        # Highest blocked stock
        if (
            "stock" in q
            and "bloqu" in q
            and any(
                term in q
                for term in (
                    "plus",
                    "maximum",
                    "max",
                    "highest",
                )
            )
            and highest_blocked
        ):
            lines.extend(
                [
                    (
                        "Supplier with highest blocked stock: "
                        f"{highest_blocked.name}"
                    ),
                    (
                        "Blocked stock EUR: "
                        f"{highest_blocked.blocked_stock_eur}"
                    ),
                ]
            )
            return "\n".join(lines)

        # Total blocked stock
        if (
            "stock" in q
            and "bloqu" in q
            and any(
                term in q
                for term in (
                    "total",
                    "combien",
                    "montant",
                )
            )
        ):
            lines.append(
                "Total blocked stock EUR: "
                f"{total_blocked_stock:.2f}"
            )
            return "\n".join(lines)

        # Supplier name lookup
        matching_suppliers = [
            supplier
            for supplier in suppliers
            if supplier.name.lower() in q
        ]

        if matching_suppliers:
            for supplier in matching_suppliers:
                orders = orders_by_supplier.get(
                    supplier.id,
                    [],
                )

                delayed = delayed_by_supplier.get(
                    supplier.id,
                    [],
                )

                delay_rate = (
                    len(delayed) / len(orders) * 100
                    if orders
                    else 0
                )

                delay_days = [
                    (
                        po.confirmed_date
                        - po.requested_date
                    ).days
                    for po in delayed
                ]

                average_delay = (
                    sum(delay_days) / len(delay_days)
                    if delay_days
                    else 0
                )

                lines.extend(
                    [
                        f"Supplier: {supplier.name}",
                        f"Country: {supplier.country}",
                        f"Risk level: {supplier.risk_level}",
                        (
                            "Blocked stock EUR: "
                            f"{supplier.blocked_stock_eur}"
                        ),
                        (
                            "Total purchase orders: "
                            f"{len(orders)}"
                        ),
                        (
                            "Delayed purchase orders: "
                            f"{len(delayed)}"
                        ),
                        f"Delay rate: {delay_rate:.2f}%",
                        (
                            "Average delay days: "
                            f"{average_delay:.2f}"
                        ),
                    ]
                )

            return "\n".join(lines)

        # Compact fallback
        lines.extend(
            [
                f"Total suppliers: {total_suppliers}",
                (
                    "Low risk suppliers: "
                    f"{risk_counts.get('low', 0)}"
                ),
                (
                    "Medium risk suppliers: "
                    f"{risk_counts.get('medium', 0)}"
                ),
                (
                    "High risk suppliers: "
                    f"{risk_counts.get('high', 0)}"
                ),
                (
                    "Total blocked stock EUR: "
                    f"{total_blocked_stock:.2f}"
                ),
                (
                    "Total purchase orders: "
                    f"{len(purchase_orders)}"
                ),
                (
                    "Total delayed purchase orders: "
                    f"{total_delayed_orders}"
                ),
            ]
        )

        return "\n".join(lines)

    finally:
        db.close()
