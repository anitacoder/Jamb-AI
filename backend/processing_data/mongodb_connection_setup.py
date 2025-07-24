import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JambDb:
    def __init__(self, mongo_url: str, db_name: str):
        self.mongo_url = mongo_url
        self.db_name = db_name

        self.collections = {
            'raw_documents': 'raw_documents',
            'processed_questions': 'processed_questions',
            'scraped_urls': 'scraped_urls',
            'metadata_log': 'metadata_log',
        }
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(
                self.mongo_url,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=1000,
                connectTimeoutMS=5000,
            )
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Connected to {self.db_name} database")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB database connection failed: {e}")
            return False

    def create_data_collections(self):
        try:
            for collection_key in self.collections.values():
                collection = self.db[collection_key]

                if collection_key == "raw_documents":
                    collection.create_index("source", unique=True, background=True)
                    collection.create_index("type", background=True)
                    collection.create_index("collected_at", background=True)
                    collection.create_index("content_hash", unique=True, background=True)

                elif collection_key == 'processed_questions':
                    collection.create_index("question_id", unique=True, background=True)
                    collection.create_index("year", background=True)
                    collection.create_index("subject", background=True)
                    collection.create_index("question_type", background=True)

                elif collection_key == 'scraped_urls':
                    collection.create_index("url", unique=True, background=True)
                    collection.create_index("scraped_at", background=True)
                    collection.create_index("content_type", background=True)

                elif collection_key == 'metadata_log':
                    collection.create_index("collection_name", background=True)
                    collection.create_index("created_at", background=True)

                logger.info(f"Collection '{collection_key}' created and indexes added (if applicable).")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    def get_collection(self, collection_logical_name: str):
        if self.db is None:
            logger.error("No database connection. Call .connect() first.")
            return None

        if collection_logical_name not in self.collections:
            logger.error(f"Collection '{collection_logical_name}' not defined in JambDb.collections.")
            return None

        return self.db[self.collections[collection_logical_name]]

    def test_connection(self):
        try:
            stats = self.db.command("dbstats")
            collection_info = {}

            for logical_name, collection_key in self.collections.items():
                collection = self.db[collection_key]
                collection_info[logical_name] = {
                    'indexes': [idx['name'] for idx in collection.list_indexes()],
                    'document_count': collection.count_documents({})
                }

            db_info = {
                'database_name': self.db_name,
                'connection_status': 'Connected',
                'database_size_bytes': stats.get('dataSize', 0),
                'collections': collection_info
            }

            logger.info("Database connection test successful.")
            return db_info

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return None

    def close_connection(self):
        if self.client:
            self.client.close()
            logger.info("Database connection closed.")

def setup_jamb_db():
    mongo_url = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "jamb")

    db = JambDb(mongo_url, db_name)

    if not db.connect():
        logger.error("Failed to connect to database.")
        return None

    if not db.create_data_collections():
        logger.error("Failed to create data collections.")
        pass # The original had a pass here, keeping for consistency.

    db_info = db.test_connection()

    if db_info:
        logger.info("Database setup completed successfully.")
        print(f"\n--- MongoDB Database Setup Report ---")
        print(f"Database Name: {db_info['database_name']}")
        print(f"Status: {db_info['connection_status']}")
        print(f"Database Size: {db_info['database_size_bytes']} bytes")
        print("\nCollections:")
        for name, info in db_info['collections'].items():
            print(f"  - {name} (Documents: {info['document_count']}, Indexes: {', '.join(info['indexes'])})")
        print(f"-------------------------------------\n")
    else:
        logger.error("Database setup verification failed.")

    return db

if __name__ == "__main__":
    jamb_db_instance = setup_jamb_db()

    if jamb_db_instance:
        print("JAMB Database initialized and ready.")
    else:
        print("JAMB Database initialization failed.")