from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.embeddings import generate_embedding

DOCUMENTS = [
    {
        "title": "Supplier Alpha delay",
        "content": (
            "Supplier Alpha has recurring supplier delivery delays and late deliveries. "
            "Orders from Supplier Alpha arrive on average 8 days late. "
            "Supplier Alpha is therefore considered a supplier with delivery delay risk. "
            "Le fournisseur Alpha présente des retards de livraison récurrents. "
            "Les commandes du fournisseur Alpha arrivent en moyenne avec 8 jours de retard. "
            "Alpha est donc un fournisseur présentant un risque de retard de livraison."
        ),
        "source": "demo",
    },
    {
        "title": "Supplier Beta performance",
        "content": (
            "Supplier Beta delivers orders on time with excellent delivery performance. "
            "Le fournisseur Beta livre ses commandes à temps avec une excellente "
            "performance de livraison."
        ),
        "source": "demo",
    },
    {
        "title": "Blocked stock",
        "content": (
            "The warehouse currently has 25000 euros of blocked automotive components. "
            "L'entrepôt dispose actuellement de 25000 euros de composants automobiles "
            "en stock bloqué."
        ),
        "source": "demo",
    },
]

db = SessionLocal()

try:
    for item in DOCUMENTS:
        document = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.title == item["title"])
            .one_or_none()
        )

        embedding = generate_embedding(item["content"])

        if document:
            document.content = item["content"]
            document.source = item["source"]
            document.embedding = embedding
            print(f"Updated: {item['title']}")
        else:
            db.add(
                KnowledgeDocument(
                    title=item["title"],
                    content=item["content"],
                    source=item["source"],
                    embedding=embedding,
                )
            )
            print(f"Created: {item['title']}")

    db.commit()
    print("Knowledge base seeded successfully.")

finally:
    db.close()
