import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

Base = declarative_base()
# 
class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    content = Column(Text)

class InteractionCount(Base):
    __tablename__ = 'interaction_count'
    id = Column(Integer, primary_key=True)
    count = Column(Integer)

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages):
        pass

class OpenAILLM(BaseLLM):
    def __init__(self, model="gpt-3.5-turbo", temperature=0.7):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv('OPENAI_API_KEY')
        )

    def generate(self, messages):
        response = self.llm.invoke(messages)
        return response.content

class Agent:
    def __init__(self, llm: BaseLLM, db_name='agent_memory.db'):
        self.llm = llm
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.interaction_count = self.get_interaction_count()

    def get_interaction_count(self):
        with self.Session() as session:
            count = session.query(InteractionCount).first()
            if not count:
                count = InteractionCount(id=1, count=0)
                session.add(count)
                session.commit()
            return count.count

    def update_interaction_count(self):
        with self.Session() as session:
            count = session.query(InteractionCount).first()
            count.count = self.interaction_count
            session.commit()

    def add_to_memory(self, memory_type, content):
        with self.Session() as session:
            memory = Memory(type=memory_type, content=content)
            session.add(memory)
            session.commit()

    def get_recent_memories(self, limit=10):
        with self.Session() as session:
            memories = session.query(Memory).order_by(Memory.id.desc()).limit(limit).all()
            return [f"{mem.type}: {mem.content}" for mem in memories]

    def talk(self, user_input):
        relevant_context = self.get_relevant_context(user_input)
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions. Use this context to inform your responses."},
            {"role": "system", "content": f"Context: {relevant_context}"},
            {"role": "user", "content": user_input}
        ]
        agent_response = self.llm.generate(messages)
        self.add_to_memory('user_input', user_input)
        self.add_to_memory('agent_response', agent_response)
        self.interaction_count += 1
        self.update_interaction_count()
        if self.interaction_count % 5 == 0:
            self.generate_reflection()
        return agent_response

    def generate_reflection(self):
        reflection_prompt = "Reflect on your recent conversations and provide a thought about your overall goals or interactions."
        recent_memories = ' '.join(self.get_recent_memories(5))
        messages = [
            {"role": "system", "content": "You are reflecting on your past experiences to gain insight."},
            {"role": "system", "content": f"Memory: {recent_memories}"},
            {"role": "user", "content": reflection_prompt}
        ]
        reflection = self.llm.generate(messages)
        self.add_to_memory('reflection', reflection)
        print(f"Agent reflection: {reflection}")

    def inject_thought(self, thought):
        self.add_to_memory('thought', thought)

    def show_memory(self):
        return self.get_recent_memories()

    def get_relevant_context(self, user_input):
        recent_memories = self.get_recent_memories()
        relevant_memories = []
        for memory in reversed(recent_memories):
            if any(word in memory.lower() for word in user_input.lower().split()):
                relevant_memories.append(memory)
        return " ".join(relevant_memories[-3:])

    def list_all_memories(self):
        """
        Retrieve all memories from the database without the agent being aware.
        This method doesn't update the interaction count or trigger any agent logic.
        """
        with self.Session() as session:
            memories = session.query(Memory).order_by(Memory.id.asc()).all()
            return [f"ID: {mem.id}, Type: {mem.type}, Content: {mem.content}" for mem in memories]
