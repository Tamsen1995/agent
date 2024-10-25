import pygame
import sys
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from abc import ABC, abstractmethod

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Agent Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

sprite_path = os.path.join(os.path.dirname(__file__), 'characters.png')
sprite_sheet = pygame.image.load(sprite_path)

agent_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
agent_sprite.blit(sprite_sheet, (0, 0), (0, 0, 16, 16))
agent_sprite = pygame.transform.scale(agent_sprite, (48, 48))  

agent_pos = [WIDTH // 2, HEIGHT // 2]

clock = pygame.time.Clock()

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
            {"role": "system", "content": f"Memory: {' '.join(self.memory[-5:])}"},
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
        for memory in reversed(self.memory[-10:]):
            if any(word in memory.lower() for word in user_input.lower().split()):
                relevant_memories.append(memory)
        return " ".join(relevant_memories[-3:])

llm = OpenAILLM()
ai_agent = Agent(llm)

show_bubble = False
agent_response = ""
bubble_duration = 200
bubble_timer = 0

def draw_speech_bubble(text, position):
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, BLACK)
    padding = 10
    bubble_width = text_surface.get_width() + padding * 2
    bubble_height = text_surface.get_height() + padding * 2

    bubble_x = position[0] + agent_sprite.get_width() // 2 - bubble_width // 2
    bubble_y = position[1] - bubble_height - 10

    pygame.draw.rect(screen, WHITE, (bubble_x, bubble_y, bubble_width, bubble_height))
    pygame.draw.rect(screen, BLACK, (bubble_x, bubble_y, bubble_width, bubble_height), 2)

    screen.blit(text_surface, (bubble_x + padding, bubble_y + padding))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_t:
                user_input = "Hello, how are you?"
                agent_response = ai_agent.talk(user_input)
                show_bubble = True
                bubble_timer = 0

    screen.fill(WHITE)

    screen.blit(agent_sprite, agent_pos)

    if show_bubble:
        draw_speech_bubble(agent_response, agent_pos)
        bubble_timer += 1
        if bubble_timer > bubble_duration:
            show_bubble = False

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()