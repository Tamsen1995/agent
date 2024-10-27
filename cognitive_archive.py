from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time
from models import Memory, Reflection, Agent

class CognitiveArchive:
    def __init__(self, Session):
        self.Session = Session

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
            return session.query(Memory)\
                .filter(Memory.agent_id == agent_id)\
                .order_by(Memory.timestamp.desc())\
                .limit(limit)\
                .all()

    def retrieve_relevant_memories(self, agent_id, context, limit=5):
        with self.Session() as session:
            return session.query(Memory)\
                .filter(
                    Memory.agent_id == agent_id,
                    Memory.content.ilike(f"%{context}%")
                )\
                .order_by(Memory.timestamp.desc())\
                .limit(limit)\
                .all()

    def generate_reflection(self, agent_id, llm):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                recent_memories = self.get_recent_memories(agent_id, limit=10)
                if recent_memories:
                    memory_strings = self.format_memories(recent_memories)
                    context = f"You are {agent.name}. Reflect on your recent experiences and draw insights or conclusions based on the following recent memories:\n\n{memory_strings}"
                    messages = [
                        {"role": "system", "content": context},
                        {"role": "user", "content": "Based on these recent experiences, what insights can you draw? How might these experiences influence your future actions or decisions?"}
                    ]
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
            return session.query(Reflection)\
                .filter(Reflection.agent_id == agent_id)\
                .order_by(Reflection.timestamp.desc())\
                .limit(limit)\
                .all()

    def format_memories(self, memories):
        return "\n".join([
            f"- [{mem.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {mem.type}: {mem.content}" 
            for mem in memories
        ])

    def format_reflections(self, reflections):
        return "\n".join([
            f"- [{datetime.fromtimestamp(ref.timestamp).strftime('%Y-%m-%d %H:%M:%S')}] Reflection: {ref.content}"
            for ref in reflections
        ])

    def get_context_for_interaction(self, agent_id, other_agent_name):
        memories = self.retrieve_relevant_memories(agent_id, other_agent_name)
        reflections = self.get_recent_reflections(agent_id, limit=3)
        
        memory_strings = self.format_memories(memories)
        reflection_strings = self.format_reflections(reflections)
        
        return memory_strings, reflection_strings

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

            combined.sort()
            return combined

    def check_and_generate_reflection(self, agent_id, llm, interaction_threshold=3):
        interaction_count = self.increment_interaction_count(agent_id)
        if interaction_count and interaction_count % interaction_threshold == 0:
            return self.generate_reflection(agent_id, llm)
        return None

    def increment_interaction_count(self, agent_id):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                agent.interaction_count += 1
                session.commit()
                return agent.interaction_count
        return None
