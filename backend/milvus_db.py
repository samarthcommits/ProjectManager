from pymilvus import connections, utility, Collection, MilvusClient
from langchain_milvus import Milvus, BaseMilvusBuiltInFunction, BM25BuiltInFunction
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from uuid import uuid4
import os
from dotenv import load_dotenv
load_dotenv()
def check_collection_size(collection_name = '', user_name = ''):
    try:
        db = MilvusClient(uri = os.environ['MILVUS_URL'], db_name=user_name, user = 'milvus', password = os.environ['MILVUS_PASSWORD'])
        answer = db.get_collection_stats(collection_name=collection_name)['row_count']
        return answer
    except Exception as e:
        print(e)
        return -1

class MilvusDB:
    def __init__(self, collection_name = 'default', user_name = 'default', embeddings = OllamaEmbeddings(model="qwen3-embedding:8b", base_url=os.environ['OLLAMA_API_ADDRESS']), auto_id = False, metadata = None):
        URI = os.environ.get('MILVUS_URL')
        print(f'URI--------------->{URI}\n\n\n')
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'])

        if not auto_id:
            auto_id = False
        database_list = db.list_databases()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'], db_name=user_name)
        if db.has_collection(collection_name=collection_name):
            self.client = Milvus(
                    embedding_function = embeddings,
                    collection_name=collection_name,
                    connection_args={"uri": URI, 'db_name':user_name},
                    auto_id=False
                )
        else:
            document = Document(
                                page_content='init',
                                metadata={}
                            )
        
            document.metadata = metadata
            # for i, doc in enumerate([documents]):
            #     doc.id = str(uuid4())
            #     doc.metadata['pages'] = '[]'
            #     doc.metadata['pdf_name'] = ''
            self.client = Milvus.from_documents(
                documents=[document],
                embedding=embeddings,
                collection_name=collection_name,
                connection_args={"uri": URI, 'db_name':user_name},
                auto_id = False
            )
        print('collection inserted', collection_name)
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)

    def add_text_docs(self, texts, metadatas=None):
        

        uuids = [str(uuid4()) for i in range(len(texts))]
        # if len(texts
        print(self.collect_num, '---------here collection num\n\n')
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)
    
    def add_text_docs_sparse(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        uuids = [str(uuid4()) for i in range(len(texts))]
        self.client.add_documents(documents=texts, ids = uuids)
        

class MilvusDB_Sparse:
    def __init__(self, collection_name = 'default', user_name = 'default'):
        URI = os.environ.get('MILVUS_URL')
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'])  

        database_list = db.list_databases()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'], db_name=user_name)

        if db.has_collection(collection_name=collection_name):
            self.client = Milvus(
                            collection_name = collection_name,
                            embedding_function = None,
                            builtin_function=BM25BuiltInFunction(
                                                input_field_names="text", output_field_names="sparse"
                                            ),
                            text_field="text",  # `text` is the input field name of BM25BuiltInFunction
                            # `sparse` is the output field name of BM25BuiltInFunction, and `dense1` and `dense2` are the output field names of embedding1 and embedding2
                            vector_field=["sparse"],
                            connection_args={
                                "uri": URI, "db_name": user_name
                            },
                            auto_id=False,
                        )
        else:
            documents = Document(
                                page_content='init',
                                metadata={}
                            )
            for i, doc in enumerate([documents]):
                doc.id = str(uuid4())
                doc.metadata['pages'] = '[]'
                doc.metadata['pdf_name'] = ''
            self.client = Milvus.from_documents(
                        documents=[documents],
                        embedding=None,
                        builtin_function=BM25BuiltInFunction(
                            input_field_names="text", output_field_names="sparse"
                        ),
                        text_field="text",  # `text` is the input field name of BM25BuiltInFunction
                        # `sparse` is the output field name of BM25BuiltInFunction, and `dense1` and `dense2` are the output field names of embedding1 and embedding2
                        vector_field=["sparse"],
                        connection_args={
                            "uri": URI, "db_name": user_name
                        },
                        drop_old=False,
                        collection_name = collection_name,
                    )
        print('client created!')
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)
        
    def add_text_docs(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        print(self.collect_num, 'here collect num sparse')
        uuids = [str(uuid4()) for i in range(len(texts))]
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)
        

class MilvusDB_ANN:
    def __init__(self, collection_name = 'default', user_name = 'default', embeddings = OllamaEmbeddings(model="qwen3-embedding:8b")):
        URI = os.environ.get('MILVUS_URL')
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'])
        database_list = db.list_databases()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        db = MilvusClient(uri=os.environ['MILVUS_URL'], user = 'milvus', password = os.environ['MILVUS_PASSWORD'], db_name=user_name)
        documents = Document(
                            page_content='init',
                            metadata={}
                        )
        
        for i, doc in enumerate([documents]):
            doc.id = str(uuid4())
            doc.metadata['pages'] = '[]'
            doc.metadata['pdf_name'] = ''
        self.client = Milvus.from_documents(
            documents=[documents],
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={"uri": URI, 'db_name':user_name},
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",            # or "L2", "IP"
                "params": {"M": 32, "efConstruction": 200}
            },
            search_params={
                "metric_type": "COSINE",
                "params": {"ef": 64}                # efSearch; keep ≥ top_k
            },
            drop_old = False
        )
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)
    def add_text_docs(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        uuids = [str(uuid4()) for i in range(len(texts))]
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)

# vector_store_saved.add_documents(documents = [Document(page_content="Third document", metadata={"source": "doc3"}),
#     Document(page_content="Fourth document", metadata={"source": "doc4"})])