import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self):
        self.interaction_count = 0
        self.reflections = []
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv('OPENAI_API_KEY'))
        self.memory = []

    def talk(self, user_input):
        relevant_context = self.get_relevant_context(user_input)
        messages = [
            {"role": "system", "content": "You are a thoughtful agent with memory of past interactions. Use this context to inform your responses."},
            {"role": "system", "content": f"Context: {relevant_context}"},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.invoke(messages)
        agent_response = response.content
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
        reflection_response = self.llm.invoke(messages)
        reflection = reflection_response.content
        self.reflections.append(f"Reflection: {reflection}")  # Store reflection in memory
        self.memory.append(f"Reflection: {reflection}")  # Also append reflection to memory
        print(f"Agent reflection: {reflection}")  # Show reflection output


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
    agent = Agent()
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
