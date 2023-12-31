from langchain import FAISS, GoogleSerperAPIWrapper, SerpAPIWrapper
from langchain.agents import Tool
from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.llms import OpenAI
from langchain.retrievers import SelfQueryRetriever
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.llms import AzureOpenAI
from langchain.document_loaders import TextLoader
from pydantic import BaseModel, Field, validator
from loguru import logger
from salesgpt.logger import time_logger
from langchain.utilities import WikipediaAPIWrapper
from langchain.tools import WikipediaQueryRun

@time_logger
def add_knowledge_base_products_to_cache(product_catalog: str = None):
    """
        We assume that the product catalog is simply a text string.
        """
    # load the document and split it into chunks
    logger.info("Inside Add Knowledge Base")
    loader = TextLoader(product_catalog, encoding='utf8')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    # embeddings = OpenAIEmbeddings(deployment="bradsol-embedding-test",chunk_size=1)
    db = FAISS.from_documents(docs, embeddings)
    db.save_local("faiss_index")

def setup_knowledge_base(product_catalog: str = None):
    print("Inside Set Up Knowledge Base")
    """
    We assume that the product catalog is simply a text string.
    """
    llm = AzureOpenAI(temperature=0.5, deployment_name="qnagpt5", model_name="gpt-35-turbo")
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    # embeddings = OpenAIEmbeddings(deployment="bradsol-embedding-test")
    db = FAISS.load_local("faiss_index", embeddings)
    knowledge_base = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=db.as_retriever()
    )
    return knowledge_base

# def duck_wrapper(input_text):
#     search = DuckDuckGoSearchRun()
#     search_results = search.run(f"site:https://columbiasportswear.co.in/ {input_text}")
#     return search_results
#
# tool = [
#     Tool(
#         name="ProductReviews",
#         func=duck_wrapper,
#         description="useful for when you need to answer questions about product reviews.",
#     ),
# ]


def get_tools(knowledge_base):
    # we only use one tool for now, but this is highly extensible!
    # search = SerpAPIWrapper()
    # wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    search = GoogleSerperAPIWrapper()

    tools = [
        Tool(
            name="ProductSearch",
            func=knowledge_base.run,
            description="useful for when you need to answer questions about product information like price , colors, size, description, image, photo and product image",
        ),
        # Tool(
        #     name="ProductOrder",
        #     func=search.run,
        #     description="useful for when you need to answer questions about product image",
        #
        # ),
        Tool(
            name="ProductReviews",
            func=search.run,
            description="useful for when you need to answer questions about product reviews from columbia sportswear browser.",
        ),

    ]

    return tools
