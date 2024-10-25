import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from abc import ABC, abstractmethod

# Load environment variables from .env file
load_dotenv()

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages):
        pass

class OpenAILLM(BaseLLM):
    def __init__(self, model="gpt-3.5-turbo", temperature=0.7):
        self.llm = ChatOpenAI(model=model, temperature=temperature, api_key=os.getenv('OPENAI_API_KEY'))

    def generate(self, messages):
        response = self.llm.invoke(messages)
        return response.content

class Agent:
    def __init__(self, llm: BaseLLM):
        self.interaction_count = 0
        self.reflections = []
        self.llm = llm
        self.memory = []

    def talk(self, user_input):
        relevant_context = self.get_relevant_context(user_input)
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions. Use this context to inform your responses."},
            {"role": "system", "content": f"Context: {relevant_context}"},
            {"role": "user", "content": user_input}
        ]
        agent_response = self.llm.generate(messages)
        self.memory.append(f"User said: {user_input}")
        self.memory.append(f"Agent responded: {agent_response}")
        self.interaction_count += 1
        if self.interaction_count % 5 == 0:
            self.generate_reflection()
        return agent_response
    
    def generate_reflection(self):
        reflection_prompt = "Reflect on your recent conversations and provide a thought about your overall goals or interactions."
        messages = [
            {"role": "system", "content": "You are reflecting on your past experiences to gain insight."},
            {"role": "system", "content": f"Memory: {' '.join(self.memory[-5:])}"},  # Use last 5 memories for context
            {"role": "user", "content": reflection_prompt}
        ]
        reflection = self.llm.generate(messages)
        self.reflections.append(f"Reflection: {reflection}")
        self.memory.append(f"Reflection: {reflection}")
        print(f"Agent reflection: {reflection}")

    def inject_thought(self, thought):
        self.memory.append(f"Thought: {thought}")

    def show_memory(self):
        return self.memory

    def get_relevant_context(self, user_input):
        relevant_memories = []
        for memory in reversed(self.memory[-10:]):  # Check last 10 memories
            if any(word in memory.lower() for word in user_input.lower().split()):
                relevant_memories.append(memory)
        return " ".join(relevant_memories[-3:])  # Return up to 3 most recent relevant memories

def main():
    llm = OpenAILLM()  # Create an instance of OpenAILLM
    agent = Agent(llm)  # Pass the LLM instance to the Agent
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        elif user_input.lower().startswith("inject"):
            thought = user_input.replace("inject", "").strip()
            agent.inject_thought(thought)
            print(f"Thought injected: {thought}")
        elif user_input.lower() == "show memory":
            for memory in agent.show_memory():
                print(memory)
        else:
            print(f"Agent: {agent.talk(user_input)}")

if __name__ == "__main__":
    main()
