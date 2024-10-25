import pygame
import sys
import os
from agent_logic import Agent, OpenAILLM

pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Agent Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

sprite_path = os.path.join(os.path.dirname(__file__), 'characters.png')
sprite_sheet = pygame.image.load(sprite_path)

agent_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
agent_sprite.blit(sprite_sheet, (0, 0), (0, 0, 16, 16))
agent_sprite = pygame.transform.scale(agent_sprite, (32, 32))  

agent_pos = [WIDTH // 3, HEIGHT // 3]  # Changed from [WIDTH // 2, HEIGHT // 2]

clock = pygame.time.Clock()

llm = OpenAILLM()
ai_agent = Agent(llm)

show_bubble = False
agent_response = ""
bubble_duration = 200
bubble_timer = 0

input_active = False
user_text = ''
input_box = pygame.Rect(100, HEIGHT - 40, WIDTH - 200, 30)
font = pygame.font.Font(None, 20)

def draw_speech_bubble(text, position):
    max_width = 300
    words = text.split(' ')
    lines = []
    font_height = font.get_height()
    line = ''
    for word in words:
        test_line = line + word + ' '
        if font.size(test_line)[0] <= max_width - 20:
            line = test_line
        else:
            lines.append(line)
            line = word + ' '
    lines.append(line)

    padding = 10
    bubble_width = max(font.size(l)[0] for l in lines) + padding * 2
    bubble_height = font_height * len(lines) + padding * 2

    bubble_x = position[0] + agent_sprite.get_width() // 2 - bubble_width // 2
    bubble_y = position[1] - bubble_height - 10

    pygame.draw.rect(screen, WHITE, (bubble_x, bubble_y, bubble_width, bubble_height))
    pygame.draw.rect(screen, BLACK, (bubble_x, bubble_y, bubble_width, bubble_height), 2)

    for i, line in enumerate(lines):
        text_surface = font.render(line, True, BLACK)
        screen.blit(
            text_surface,
            (bubble_x + padding, bubble_y + padding + i * font_height)
        )

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if input_active:
                if event.key == pygame.K_RETURN:
                    if user_text:
                        agent_response = ai_agent.talk(user_text)
                        show_bubble = True
                        bubble_timer = 0
                        user_text = ''
                    input_active = False
                elif event.key == pygame.K_ESCAPE:
                    input_active = False
                    user_text = ''
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode
            else:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_t:
                    input_active = True

    screen.fill(WHITE)
    screen.blit(agent_sprite, agent_pos)

    if input_active:
        pygame.draw.rect(screen, WHITE, input_box)
        pygame.draw.rect(screen, BLACK, input_box, 2)
        text_surface = font.render(user_text, True, BLACK)
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))

    if show_bubble:
        draw_speech_bubble(agent_response, agent_pos)
        bubble_timer += 1
        if bubble_timer > bubble_duration:
            show_bubble = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
