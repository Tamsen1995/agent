import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from cognitive_archive import CognitiveArchive
from models import Base, Agent, Memory, Reflection

load_dotenv()

class AgentManager:
    def __init__(self, db_name='agent_database.db'):
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.cognitive_archive = CognitiveArchive(self.Session)

    def create_agent(self, name):
        with self.Session() as session:
            new_agent = Agent(name=name)
            session.add(new_agent)
            session.commit()
            return new_agent.id

    def get_all_agents(self):
        with self.Session() as session:
            return session.query(Agent).all()

    def get_agent(self, agent_id):
        with self.Session() as session:
            return session.query(Agent).get(agent_id)

    def talk(self, agent_id, user_input):
        memory_strings, reflection_strings = self.cognitive_archive.get_context_for_interaction(agent_id, user_input)
        
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions and reflections. Use this context to inform your responses."},
            {"role": "system", "content": f"Memories:\n{memory_strings}\n\nReflections:\n{reflection_strings}"},
            {"role": "user", "content": user_input}
        ]
        llm = OpenAILLM()
        agent_response = llm.generate(messages)
        self.cognitive_archive.add_memory(agent_id, 'user_input', user_input)
        self.cognitive_archive.add_memory(agent_id, 'agent_response', agent_response)
        self.cognitive_archive.check_and_generate_reflection(agent_id, llm)
        return agent_response

    def agent_interaction(self, agent1_id, agent2_id, num_exchanges=3):
        with self.Session() as session:
            agent1 = session.query(Agent).get(agent1_id)
            agent2 = session.query(Agent).get(agent2_id)
            if agent1 and agent2:
                llm = OpenAILLM()
                full_interaction = []
                
                for i in range(num_exchanges):
                    # Agent 1's turn
                    memory_strings1, reflection_strings1 = self.cognitive_archive.get_context_for_interaction(agent1_id, agent2.name)
                    prompt_agent1 = self.create_interaction_prompt(agent1.name, agent2.name, memory_strings1, reflection_strings1, full_interaction)
                    response1 = llm.generate(prompt_agent1)
                    full_interaction.append(f"{agent1.name}: {response1}")
                    self.cognitive_archive.add_memory(agent1_id, 'interaction', f"{agent1.name}: {response1}")

                    # Agent 2's turn
                    memory_strings2, reflection_strings2 = self.cognitive_archive.get_context_for_interaction(agent2_id, agent1.name)
                    prompt_agent2 = self.create_interaction_prompt(agent2.name, agent1.name, memory_strings2, reflection_strings2, full_interaction)
                    response2 = llm.generate(prompt_agent2)
                    full_interaction.append(f"{agent2.name}: {response2}")
                    self.cognitive_archive.add_memory(agent2_id, 'interaction', f"{agent2.name}: {response2}")

                # Generate reflections
                reflection1 = self.cognitive_archive.generate_reflection(agent1_id, llm)
                reflection2 = self.cognitive_archive.generate_reflection(agent2_id, llm)

                return "\n".join(full_interaction), reflection1, reflection2
        return None, None, None

    def create_interaction_prompt(self, agent_name, other_agent_name, memories, reflections, conversation_history):
        context = f"You are {agent_name}. You are having a conversation with {other_agent_name}. Use the following memories and reflections to guide your responses:\n\nMemories:\n{memories}\n\nReflections:\n{reflections}"
        prompt = [
            {"role": "system", "content": context},
            {"role": "system", "content": "Here's the conversation so far:"}
        ]
        
        for exchange in conversation_history:
            prompt.append({"role": "assistant", "content": exchange})
        
        prompt.append({"role": "assistant", "content": f"Continue the conversation as {agent_name}. Respond to {other_agent_name}'s last message or start a new topic if appropriate."})
        
        return prompt

    def delete_agent(self, agent_id):
        with self.Session() as session:
            agent = session.query(Agent).get(agent_id)
            if agent:
                session.query(Memory).filter(Memory.agent_id == agent_id).delete()
                session.query(Reflection).filter(Reflection.agent_id == agent_id).delete()
                session.delete(agent)
                session.commit()
                return True
            return False

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
