import os
import sqlite3
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import uuid

load_dotenv()

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
        self.init_db()
        self.interaction_count = self.get_interaction_count()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS memories
                          (id INTEGER PRIMARY KEY, type TEXT, content TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS interaction_count
                          (id INTEGER PRIMARY KEY, count INTEGER)''')
        cursor.execute('INSERT OR IGNORE INTO interaction_count (id, count) VALUES (1, 0)')
        conn.commit()
        conn.close()

    def get_interaction_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT count FROM interaction_count WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def update_interaction_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE interaction_count SET count = ? WHERE id = 1',
                       (self.interaction_count,))
        conn.commit()
        conn.close()

    def add_to_memory(self, memory_type, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO memories (type, content) VALUES (?, ?)', (memory_type, content))
        conn.commit()
        conn.close()

    def get_recent_memories(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT type, content FROM memories ORDER BY id DESC LIMIT ?', (limit,))
        memories = cursor.fetchall()
        conn.close()
        return [f"{mem_type}: {content}" for mem_type, content in memories]

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
