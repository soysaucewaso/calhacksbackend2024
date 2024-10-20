GOOGLE_API_KEY = ""

from langchain_core.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
class rag_model:
    def __init__(self, context):
        self.model = ChatGoogleGenerativeAI(model="gemini-pro",google_api_key=GOOGLE_API_KEY,
                                 temperature=0.2,convert_system_message_to_human=True)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        self.context = context
        texts = text_splitter.split_text(context)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=GOOGLE_API_KEY)
        self.vector_index = Chroma.from_texts(texts, embeddings).as_retriever(search_kwargs={"k":5})
#         self.template = """
# You are a highly positive and empathetic assistant. Based on the given context You need to cheer up the user of he is already doing somthing like that.
# Context:
# {context}
#
# User: {question}
# Positive, Supportive Response to cheer up the user:
# """

    def prompt(self,question, chat_lis):

        chat_history = ""
        for pair in chat_lis:
            for key, value in pair.items():
                chat_history += f"{key} {value}\n"


        qa_chain = RetrievalQA.from_chain_type(
            self.model,
            retriever=self.vector_index,
            return_source_documents=False,
            # chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        events = qa_chain.invoke({"query": f"Get all the context related to all the following words individually {question} in the context"})[
            'result']

        print(events)
        template = f"""
         You are a chatbot that helps the users by mentally making people feel better.
         You are given the following events from a persons life: {events} 
         """

        template += """
        {context} 
         You need to generate answer by try connecting existing question with one of the events and make the user feel better by only highlighting the things he is doing better.
         Be as concise and short as possible.
          here's the conversation so far:"""

        template += f"""{chat_history}\n"""

        template += """  User: {question}
          Assistant:
         """

        QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

        q = RetrievalQA.from_chain_type(
            self.model,
            retriever=self.vector_index,
            return_source_documents=False,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )

        return q({"query": question})['result']

        # print(question)
        # pompt = f"From the following prompt identify the activity user is not doing. only mention the activities name.{question}"
        # topic = model_2.generate_content(pompt).candidates[0].content.parts[0].text
        # print(topic)
        # #QA_CHAIN_PROMPT = PromptTemplate.from_template(self.template)
        # qa_chain = RetrievalQA.from_chain_type(
        #     self.model,
        #     retriever=self.vector_index,
        #     return_source_documents=False,
        #    # chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        # )
        # positives = qa_chain.invoke({"query": f"All the {topic} in the context"})['result']
        # print(positives)
        # prompt = f"""
        # You are an affirmative chatbot that always emotionally helps the user.
        # Provide the user with a affirmative response to user's query {question}. Because he has been doing {positives}.
        # Your response should start by comforting the user and keep the respnse concise.
        # """
        #
        # prompt = f"""
        # context: {self.context}
        #
        # Based on the user's previous achievements, guide the conversation by acknowledging
        # their growth or progress. if the user is discussing a new challenge, recall how
        # they overcame past obstacles and offer a connection to the current struggle.
        #
        # User: {question}
        # """
        # return model_2.generate_content(prompt).candidates[0].content.parts[0].text

    def get_positive(self):
        qa_chain = RetrievalQA.from_chain_type(
            self.model,
            retriever=self.vector_index,
            return_source_documents=False,
            # chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        model_2 = genai.GenerativeModel(model_name="gemini-pro")

        positive = qa_chain.invoke({"query": f"Get one thing from the context that the user is doing good from the context."})['result']
        return model_2.generate_content(f"Reformat the following such that it directly talks about the user. {positive}").candidates[0].content.parts[0].text

