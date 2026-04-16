import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from sentence_transformers import SentenceTransformer
from core.database.manager import DatabaseManager
from config.settings import settings
import re

class KnowledgeIngestor:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.embed_model = SentenceTransformer(settings.EMBED_MODEL_NAME)
        
    async def scrape_and_ingest(self, start_url: str, max_pages: int = 10):
        print(f"[INGEST] Starting scrape for: {start_url}")
        
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(
            cache_mode="bypass",
            word_count_threshold=50
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # For simplicity, we'll start with the main page. 
            # In a full crawler, we'd recursively follow links.
            result = await crawler.arun(url=start_url, config=run_config)
            
            if result.success:
                print(f"[INGEST] Successfully scraped {start_url}")
                await self._process_content(start_url, result.markdown, result.metadata.get("title", "Fastigo"))
            else:
                print(f"[ERROR] Failed to scrape {start_url}: {result.error_message}")

    async def _process_content(self, url: str, content: str, title: str):
        # 1. Clean and Chunk Content
        chunks = self._chunk_text(content)
        print(f"[INGEST] Processing {len(chunks)} chunks for {url}")
        
        # 2. Embed and Store
        for chunk in chunks:
            if len(chunk.strip()) < 100:
                continue
                
            embedding = self.embed_model.encode(chunk).tolist()
            
            # Use Supabase to store
            self.db.supabase_client.table("website_knowledge").insert({
                "url": url,
                "title": title,
                "content": chunk,
                "embedding": embedding
            }).execute()
            
        print(f"[INGEST] Completed ingestion for {url}")

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        # Simple character-based recursive chunking
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

# Example usage (can be triggered by API)
if __name__ == "__main__":
    db = DatabaseManager()
    ingestor = KnowledgeIngestor(db)
    asyncio.run(ingestor.scrape_and_ingest("https://fastigo.co/"))
