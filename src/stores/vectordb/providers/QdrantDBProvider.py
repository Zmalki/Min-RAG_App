
from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from uuid import uuid4


class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str):

        self.client = None
        self.db_path = db_path
        self.distance_method = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)


    def list_all_collections(self) -> list:
      return self.client.get_collections().collections
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name=collection_name)


    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
        
        if not self.is_collection_existed(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )

            return True
        
        return False


    def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict | None = None,
        record_id: str | None = None,
    ):
        if not self.is_collection_existed(collection_name):
            self.logger.error(
                f"Cannot insert into non-existing collection: {collection_name}"
            )
            return False

        try:
            point_id = record_id or str(uuid4())

            self.client.upload_points(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "text": text,
                            "metadata": metadata or {},
                        },
                    )
                ],
            )
        except Exception as e:
            self.logger.error(f"Error while inserting record: {e}")
            return False

        return True

    def insert_many(
        self,
        collection_name: str,
        texts: list[str],
        vectors: list[list[float]],
        metadata: list[dict | None] | None = None,
        record_ids: list[str | None] | None = None,
        batch_size: int = 50,
    ) -> bool:
        if not self.is_collection_existed(collection_name):
            self.logger.error(
                f"Cannot insert into non-existing collection: {collection_name}"
            )
            return False

        if batch_size <= 0:
            self.logger.error("batch_size must be greater than 0")
            return False

        if len(texts) != len(vectors):
            self.logger.error("texts and vectors must have the same length")
            return False

        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = [None] * len(texts)

        if len(metadata) != len(texts) or len(record_ids) != len(texts):
            self.logger.error(
                "texts, vectors, metadata, and record_ids must have matching lengths"
            )
            return False

        for start in range(0, len(texts), batch_size):
            end = start + batch_size

            batch_points = [
                models.PointStruct(
                    id=record_ids[i] or str(uuid4()),
                    vector=vectors[i],
                    payload={
                        "text": texts[i],
                        "metadata": metadata[i] or {},
                    },
                )
                for i in range(start, min(end, len(texts)))
            ]

            try:
                self.client.upload_points(
                    collection_name=collection_name,
                    points=batch_points,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    def search_by_vector(self, collection_name: str, vector: list[float], limit: int = 5):
        result = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return result.points