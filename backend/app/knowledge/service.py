from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

class KnowledgeQuery(BaseModel):
    query: str
    category_id: Optional[int] = None
    difficulty: Optional[str] = None
    limit: int = 5

class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: KnowledgeQuery, embedding_model=None) -> List[Dict[str, Any]]:
        if embedding_model:
            query_embedding = await embedding_model.embed(query.query)
            sql = """
                SELECT id, title, slug, content, category_id, tags, difficulty,
                       embedding <-> :query_embedding as distance
                FROM knowledge_articles
                WHERE is_published = TRUE
            """
            params = {"query_embedding": str(query_embedding), "limit": query.limit}

            if query.category_id:
                sql += " AND category_id = :category_id"
                params["category_id"] = query.category_id
            if query.difficulty:
                sql += " AND difficulty = :difficulty"
                params["difficulty"] = query.difficulty

            sql += " ORDER BY embedding <-> :query_embedding LIMIT :limit"
            result = await self.db.execute(sql, params)
            rows = result.fetchall()

            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "slug": row.slug,
                    "content": row.content[:500] + "..." if len(row.content) > 500 else row.content,
                    "tags": row.tags,
                    "difficulty": row.difficulty,
                    "relevance_score": 1.0 - float(row.distance)
                }
                for row in rows
            ]

        # Fallback: text search
        sql = """
            SELECT id, title, slug, content, category_id, tags, difficulty
            FROM knowledge_articles
            WHERE is_published = TRUE AND (title ILIKE :query OR content ILIKE :query)
        """
        params = {"query": f"%{query.query}%", "limit": query.limit}

        if query.category_id:
            sql += " AND category_id = :category_id"
            params["category_id"] = query.category_id

        sql += " LIMIT :limit"
        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "title": row.title,
                "slug": row.slug,
                "content": row.content[:500] + "..." if len(row.content) > 500 else row.content,
                "tags": row.tags,
                "difficulty": row.difficulty
            }
            for row in rows
        ]

    async def get_article(self, slug: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM knowledge_articles WHERE slug = :slug AND is_published = TRUE"
        result = await self.db.execute(sql, {"slug": slug})
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT id, title, slug, difficulty, tags
            FROM knowledge_articles
            WHERE category_id = :category_id AND is_published = TRUE
            ORDER BY title
        """
        result = await self.db.execute(sql, {"category_id": category_id})
        return [dict(row) for row in result.fetchall()]

    async def get_learning_path(self, from_difficulty: str = "beginner") -> List[Dict[str, Any]]:
        difficulties = ["beginner", "intermediate", "advanced"]
        start_idx = difficulties.index(from_difficulty) if from_difficulty in difficulties else 0

        sql = """
            SELECT id, title, slug, difficulty, category_id, prerequisites
            FROM knowledge_articles
            WHERE is_published = TRUE AND difficulty = ANY(:difficulties)
            ORDER BY
                CASE difficulty
                    WHEN 'beginner' THEN 1
                    WHEN 'intermediate' THEN 2
                    WHEN 'advanced' THEN 3
                END, title
        """
        result = await self.db.execute(sql, {"difficulties": difficulties[start_idx:]})
        return [dict(row) for row in result.fetchall()]

