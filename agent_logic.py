import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

load_dotenv()

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    x_position = Column(Float)
    y_position = Column(Float)
    memories = relationship("Memory", back_populates="agent")

class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    type = Column(String)
    content = Column(Text)
    agent = relationship("Agent", back_populates="memories")

class AgentManager:
    def __init__(self, db_name='agent_database.db'):
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_agent(self, name, x_position, y_position):
        with self.Session() as session:
            new_agent = Agent(name=name, x_position=x_position, y_position=y_position)
            session.add(new_agent)
            session.commit()
            return new_agent.id

    def get_all_agents(self):
        with self.Session() as session:
            return session.query(Agent).all()

    def update_agent_position(self, agent_id, x_position, y_position):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                agent.x_position = x_position
                agent.y_position = y_position
                session.commit()

    def add_memory(self, agent_id, memory_type, content):
        with self.Session() as session:
            memory = Memory(agent_id=agent_id, type=memory_type, content=content)
            session.add(memory)
            session.commit()

    def get_recent_memories(self, agent_id, limit=10):
        with self.Session() as session:
            memories = session.query(Memory).filter(Memory.agent_id == agent_id).order_by(Memory.id.desc()).limit(limit).all()
            return [f"{mem.type}: {mem.content}" for mem in memories]

    def talk(self, agent_id, user_input):
        relevant_context = self.get_relevant_context(agent_id, user_input)
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions. Use this context to inform your responses."},
            {"role": "system", "content": f"Context: {relevant_context}"},
            {"role": "user", "content": user_input}
        ]
        llm = OpenAILLM()
        agent_response = llm.generate(messages)
        self.add_memory(agent_id, 'user_input', user_input)
        self.add_memory(agent_id, 'agent_response', agent_response)
        return agent_response

    def get_relevant_context(self, agent_id, user_input):
        recent_memories = self.get_recent_memories(agent_id)
        relevant_memories = []
        for memory in reversed(recent_memories):
            if any(word in memory.lower() for word in user_input.lower().split()):
                relevant_memories.append(memory)
        return " ".join(relevant_memories[-3:])

    def list_all_memories(self, agent_id):
        with self.Session() as session:
            memories = session.query(Memory).filter(Memory.agent_id == agent_id).order_by(Memory.id.asc()).all()
            return [f"ID: {mem.id}, Type: {mem.type}, Content: {mem.content}" for mem in memories]

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
