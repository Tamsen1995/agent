import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv('OPENAI_API_KEY'))
        self.memory = []

    def talk(self, user_input):
        self.memory.append({"role": "user", "content": user_input})
        messages = [
            {"role": "system", "content": "You are a thoughtful agent."},
            *[{"role": m["role"], "content": m["content"]} for m in self.memory if isinstance(m, dict)]
        ]
        response = self.llm.invoke(messages)
        agent_response = response.content
        self.memory.append({"role": "assistant", "content": agent_response})
        return agent_response

    def reflect_and_store(self, user_input, agent_response):
        reflection = f"Reflection: Responded to '{user_input}' with '{agent_response}'"
        self.memory.append(reflection)

    def inject_thought(self, thought):
        self.memory.append(f"Injected thought: {thought}")

    def show_memory(self):
        return self.memory

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
