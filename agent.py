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
GRAY = (200, 200, 200)

sprite_path = os.path.join(os.path.dirname(__file__), 'characters.png')
sprite_sheet = pygame.image.load(sprite_path)

agent_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
agent_sprite.blit(sprite_sheet, (0, 0), (0, 0, 16, 16))
agent_sprite = pygame.transform.scale(agent_sprite, (32, 32))  

agent_pos = [WIDTH // 3, HEIGHT // 3]

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

# New variables for memory viewing
viewing_memories = False
memory_scroll = 0
memories = []

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

def draw_memories():
    global memory_scroll
    memory_surface = pygame.Surface((WIDTH - 100, HEIGHT - 100))
    memory_surface.fill(WHITE)
    y = 10
    for memory in memories[memory_scroll:]:
        words = memory.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= WIDTH - 120:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines:
            memory_text = font.render(line, True, BLACK)
            memory_surface.blit(memory_text, (10, y))
            y += 30
            if y > HEIGHT - 130:
                break
        y += 10  # Add some space between memories
        if y > HEIGHT - 130:
            break
    screen.blit(memory_surface, (50, 50))
    
    pygame.draw.rect(screen, GRAY, (WIDTH - 30, 50, 20, HEIGHT - 100))
    pygame.draw.polygon(screen, BLACK, [(WIDTH - 25, 60), (WIDTH - 15, 60), (WIDTH - 20, 50)])
    pygame.draw.polygon(screen, BLACK, [(WIDTH - 25, HEIGHT - 60), (WIDTH - 15, HEIGHT - 60), (WIDTH - 20, HEIGHT - 50)])

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_t and not viewing_memories and not input_active:
                input_active = True
            elif event.key == pygame.K_m and not input_active:
                viewing_memories = not viewing_memories
                if viewing_memories:
                    memories = ai_agent.list_all_memories()
                    memory_scroll = 0
            elif viewing_memories:
                if event.key == pygame.K_UP:
                    memory_scroll = max(0, memory_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    memory_scroll = min(len(memories) - 1, memory_scroll + 1)
            elif input_active:
                if event.key == pygame.K_RETURN:
                    agent_response = ai_agent.talk(user_text)
                    show_bubble = True
                    bubble_timer = bubble_duration
                    user_text = ''
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if viewing_memories:
                if WIDTH - 30 <= event.pos[0] <= WIDTH - 10:
                    if 50 <= event.pos[1] <= 70:
                        memory_scroll = max(0, memory_scroll - 1)
                    elif HEIGHT - 70 <= event.pos[1] <= HEIGHT - 50:
                        memory_scroll = min(len(memories) - 1, memory_scroll + 1)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        agent_pos[0] = max(agent_pos[0] - 5, 0)
    if keys[pygame.K_RIGHT]:
        agent_pos[0] = min(agent_pos[0] + 5, WIDTH - agent_sprite.get_width())
    if keys[pygame.K_UP]:
        agent_pos[1] = max(agent_pos[1] - 5, 0)
    if keys[pygame.K_DOWN]:
        agent_pos[1] = min(agent_pos[1] + 5, HEIGHT - agent_sprite.get_height())

    screen.fill(WHITE)
    screen.blit(agent_sprite, agent_pos)

    if show_bubble:
        draw_speech_bubble(agent_response, agent_pos)
        bubble_timer -= 1
        if bubble_timer <= 0:
            show_bubble = False

    if input_active:
        pygame.draw.rect(screen, BLACK, input_box, 2)
        text_surface = font.render(user_text, True, BLACK)
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))

    if viewing_memories:
        draw_memories()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
