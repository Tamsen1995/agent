import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import time

load_dotenv()

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    x_position = Column(Float)
    y_position = Column(Float)
    interaction_count = Column(Integer, default=0)
    memories = relationship("Memory", back_populates="agent")
    reflections = relationship("Reflection", back_populates="agent")

class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    type = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime)
    emotional_state = Column(String)
    relevance = Column(Float)
    agent = relationship("Agent", back_populates="memories")

class Reflection(Base):
    __tablename__ = 'reflections'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    content = Column(Text)
    timestamp = Column(Float)
    agent = relationship("Agent", back_populates="reflections")

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

    def add_memory(self, agent_id, memory_type, content, emotional_state="neutral", relevance=0.5):
        with self.Session() as session:
            memory = Memory(
                agent_id=agent_id,
                type=memory_type,
                content=content,
                timestamp=datetime.now(),
                emotional_state=emotional_state,
                relevance=relevance
            )
            session.add(memory)
            session.commit()

    def get_recent_memories(self, agent_id, limit=10):
        with self.Session() as session:
            memories = session.query(Memory)\
                .filter(Memory.agent_id == agent_id)\
                .order_by(Memory.timestamp.desc())\
                .limit(limit)\
                .all()
            return memories  # Return Memory objects instead of strings

    def retrieve_relevant_memories(self, agent_id, context, limit=5):
        with self.Session() as session:
            relevant_memories = session.query(Memory)\
                .filter(
                    Memory.agent_id == agent_id,
                    Memory.content.ilike(f"%{context}%")
                )\
                .order_by(Memory.timestamp.desc())\
                .limit(limit)\
                .all()
            return relevant_memories

    def talk(self, agent_id, user_input):
        # Retrieve relevant memories
        relevant_memories = self.retrieve_relevant_memories(agent_id, user_input)
        memory_strings = "\n".join([
            f"- [{mem.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {mem.type}: {mem.content}" 
            for mem in relevant_memories
        ])
        
        # Retrieve recent reflections
        recent_reflections = self.get_recent_reflections(agent_id, limit=3)
        reflection_strings = "\n".join([
            f"- [{datetime.fromtimestamp(ref.timestamp).strftime('%Y-%m-%d %H:%M:%S')}] Reflection: {ref.content}"
            for ref in recent_reflections
        ])
        
        # Construct messages with both memories and reflections
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions and reflections. Use this context to inform your responses."},
            {"role": "system", "content": f"Memories:\n{memory_strings}\n\nReflections:\n{reflection_strings}"},
            {"role": "user", "content": user_input}
        ]
        llm = OpenAILLM()
        agent_response = llm.generate(messages)
        self.add_memory(agent_id, 'user_input', user_input)
        self.add_memory(agent_id, 'agent_response', agent_response)
        return agent_response

    def agent_interaction(self, agent1_id, agent2_id):
        with self.Session() as session:
            agent1 = session.query(Agent).get(agent1_id)
            agent2 = session.query(Agent).get(agent2_id)
            if agent1 and agent2:
                # Retrieve relevant memories
                memories1 = self.retrieve_relevant_memories(agent1_id, agent2.name)
                memories2 = self.retrieve_relevant_memories(agent2_id, agent1.name)
                
                # Retrieve recent reflections
                reflections1 = self.get_recent_reflections(agent1_id, limit=3)
                reflections2 = self.get_recent_reflections(agent2_id, limit=3)

                # Generate prompts including memories and reflections
                prompt_agent1 = self.create_interaction_prompt(agent1.name, agent2.name, memories1, reflections1)
                prompt_agent2 = self.create_interaction_prompt(agent2.name, agent1.name, memories2, reflections2)

                llm = OpenAILLM()

                # Generate responses
                response1 = llm.generate(prompt_agent1)
                response2 = llm.generate(prompt_agent2)

                # Store memories of the interaction
                self.add_memory(agent1_id, 'interaction', f"{agent1.name}: {response1}")
                self.add_memory(agent2_id, 'interaction', f"{agent2.name}: {response2}")

                # After successful interaction, check for reflection
                reflection1 = self.check_and_generate_reflection(agent1_id)
                reflection2 = self.check_and_generate_reflection(agent2_id)

                full_interaction = f"{agent1.name}: {response1}\n{agent2.name}: {response2}"
                return full_interaction, reflection1, reflection2
        return "No interaction occurred.", None, None

    def create_interaction_prompt(self, agent_name, other_agent_name, memories, reflections):
        memory_strings = "\n".join([
            f"- [{mem.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {mem.type}: {mem.content}" 
            for mem in memories
        ])
        reflection_strings = "\n".join([
            f"- [{datetime.fromtimestamp(ref.timestamp).strftime('%Y-%m-%d %H:%M:%S')}] Reflection: {ref.content}"
            for ref in reflections
        ])
        context = f"You are {agent_name}. You are interacting with {other_agent_name}. Use the following memories and reflections to guide your response:\n\nMemories:\n{memory_strings}\n\nReflections:\n{reflection_strings}"
        prompt = [
            {"role": "system", "content": context},
            {"role": "assistant", "content": f"{other_agent_name} says: Hello!"},
            {"role": "assistant", "content": "Compose your reply."}
        ]
        return prompt

    def delete_agent(self, agent_id):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                # Delete associated memories and reflections first
                session.query(Memory).filter(Memory.agent_id == agent_id).delete()
                session.query(Reflection).filter(Reflection.agent_id == agent_id).delete()
                # Then delete the agent
                session.delete(agent)
                session.commit()
                return True
            return False

    def increment_interaction_count(self, agent_id):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                agent.interaction_count += 1
                session.commit()
                return agent.interaction_count
        return None

    def check_and_generate_reflection(self, agent_id, interaction_threshold=10):
        interaction_count = self.increment_interaction_count(agent_id)
        if interaction_count and interaction_count % interaction_threshold == 0:
            return self.generate_reflection(agent_id)
        return None

    def generate_reflection(self, agent_id):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                recent_memories = self.get_recent_memories(agent_id, limit=10)
                if recent_memories:
                    memory_strings = "\n".join([
                        f"- [{mem.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {mem.type}: {mem.content}" 
                        for mem in recent_memories
                    ])
                    context = f"You are {agent.name}. Reflect on your recent experiences and draw insights or conclusions based on the following recent memories:\n\n{memory_strings}"
                    messages = [
                        {"role": "system", "content": context},
                        {"role": "user", "content": "Based on these recent experiences, what insights can you draw? How might these experiences influence your future actions or decisions?"}
                    ]
                    llm = OpenAILLM()
                    reflection_content = llm.generate(messages)

                    new_reflection = Reflection(
                        agent_id=agent_id,
                        content=reflection_content,
                        timestamp=time.time()
                    )
                    session.add(new_reflection)
                    session.commit()
                    return reflection_content
        return None

    def get_recent_reflections(self, agent_id, limit=5):
        with self.Session() as session:
            reflections = session.query(Reflection)\
                .filter(Reflection.agent_id == agent_id)\
                .order_by(Reflection.timestamp.desc())\
                .limit(limit)\
                .all()
            return reflections  # Return Reflection objects

    def list_all_memories_and_reflections(self, agent_id):
        with self.Session() as session:
            memories = session.query(Memory)\
                .filter(Memory.agent_id == agent_id)\
                .order_by(Memory.timestamp.asc())\
                .all()
            reflections = session.query(Reflection)\
                .filter(Reflection.agent_id == agent_id)\
                .order_by(Reflection.timestamp.asc())\
                .all()

            combined = []
            for memory in memories:
                combined.append(f"[{memory.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {memory.type}: {memory.content}")
            for reflection in reflections:
                combined.append(f"[{datetime.fromtimestamp(reflection.timestamp).strftime('%Y-%m-%d %H:%M:%S')}] Reflection: {reflection.content}")

            # Sort by timestamp
            combined.sort()
            return combined

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

