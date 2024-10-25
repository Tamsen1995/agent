import pygame
import sys
import os
from agent_logic import Agent, OpenAILLM

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
