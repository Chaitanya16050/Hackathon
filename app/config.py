from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db: str = Field(default="aidenai", alias="MONGODB_DB")

    pinecone_api_key: str | None = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_index: str = Field(default="aidenai-docs", alias="PINECONE_INDEX")
    pinecone_cloud: str = Field(default="aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_REGION")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    use_fake_embeddings: bool = Field(default=False, alias="USE_FAKE_EMBEDDINGS")
    use_memory_vectorstore: bool = Field(default=False, alias="USE_MEMORY_VECTORSTORE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
