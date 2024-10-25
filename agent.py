import pygame
import sys
import os
import random
from agent_logic import AgentManager

pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multi-Agent AI Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

sprite_path = os.path.join(os.path.dirname(__file__), 'characters.png')
sprite_sheet = pygame.image.load(sprite_path)

agent_manager = AgentManager()

agents = []
for db_agent in agent_manager.get_all_agents():
    sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
    sprite.blit(sprite_sheet, (0, 0), (random.randint(0, 3) * 16, 0, 16, 16))
    sprite = pygame.transform.scale(sprite, (32, 32))
    agents.append({
        "id": db_agent.id,
        "name": db_agent.name,
        "pos": [db_agent.x_position, db_agent.y_position],
        "sprite": sprite,
        "show_bubble": False,
        "response": "",
        "bubble_timer": 0,
        "movement_cooldown": 0,
        "personality": random.random()
    })

clock = pygame.time.Clock()

input_active = False
user_text = ''
input_box = pygame.Rect(100, HEIGHT - 40, WIDTH - 200, 30)
font = pygame.font.Font(None, 20)

viewing_memories = False
memory_scroll = 0
memories = []

def draw_speech_bubble(text, position, sprite):
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

    bubble_x = position[0] + sprite.get_width() // 2 - bubble_width // 2
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

def calculate_random_movement(current_pos, width, height):
    dx = random.randint(-20, 20)  # Increased range of movement
    dy = random.randint(-20, 20)  # Increased range of movement
    new_x = max(0, min(current_pos[0] + dx, width - 32))
    new_y = max(0, min(current_pos[1] + dy, height - 32))
    return [new_x, new_y]

running = True
selected_agent = 0 if agents else None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_n:
                # Spawn a new agent
                new_x = random.randint(0, WIDTH - 32)
                new_y = random.randint(0, HEIGHT - 32)
                new_name = f"Agent_{len(agents) + 1}"
                new_id = agent_manager.create_agent(new_name, new_x, new_y)
                new_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
                new_sprite.blit(sprite_sheet, (0, 0), (random.randint(0, 3) * 16, 0, 16, 16))
                new_sprite = pygame.transform.scale(new_sprite, (32, 32))
                agents.append({
                    "id": new_id,
                    "name": new_name,
                    "pos": [new_x, new_y],
                    "sprite": new_sprite,
                    "show_bubble": False,
                    "response": "",
                    "bubble_timer": 0,
                    "movement_cooldown": 0,
                    "personality": random.random()
                })
                selected_agent = len(agents) - 1
            elif event.key == pygame.K_t and not viewing_memories and not input_active and selected_agent is not None:
                input_active = True
            elif event.key == pygame.K_m and not input_active and selected_agent is not None:
                viewing_memories = not viewing_memories
                if viewing_memories:
                    memories = agent_manager.list_all_memories(agents[selected_agent]["id"])
                    memory_scroll = 0
            elif event.key == pygame.K_TAB:
                if agents:
                    selected_agent = (selected_agent + 1) % len(agents)
            elif viewing_memories:
                if event.key == pygame.K_UP:
                    memory_scroll = max(0, memory_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    memory_scroll = min(len(memories) - 1, memory_scroll + 1)
            elif input_active:
                if event.key == pygame.K_RETURN:
                    agent_response = agent_manager.talk(agents[selected_agent]["id"], user_text)
                    agents[selected_agent]["show_bubble"] = True
                    agents[selected_agent]["response"] = agent_response
                    agents[selected_agent]["bubble_timer"] = 200  # bubble_duration
                    user_text = ''
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode
            elif event.key == pygame.K_d and selected_agent is not None:
                # Delete the currently selected agent
                if agent_manager.delete_agent(agents[selected_agent]["id"]):
                    del agents[selected_agent]
                    if agents:
                        selected_agent = (selected_agent) % len(agents)
                    else:
                        selected_agent = None
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if viewing_memories:
                if WIDTH - 30 <= event.pos[0] <= WIDTH - 10:
                    if 50 <= event.pos[1] <= 70:
                        memory_scroll = max(0, memory_scroll - 1)
                    elif HEIGHT - 70 <= event.pos[1] <= HEIGHT - 50:
                        memory_scroll = min(len(memories) - 1, memory_scroll + 1)

    # Update agent positions
    for agent in agents:
        if agent["movement_cooldown"] <= 0:
            new_pos = calculate_random_movement(agent["pos"], WIDTH, HEIGHT)
            agent["pos"] = new_pos
            agent_manager.update_agent_position(agent["id"], new_pos[0], new_pos[1])
            
            # Set a shorter cooldown for more frequent movement
            base_cooldown = 10 + int(agent["personality"] * 20)  # 0.16 to 0.5 seconds
            agent["movement_cooldown"] = random.randint(base_cooldown, base_cooldown + 10)
        else:
            agent["movement_cooldown"] -= 1

    screen.fill(WHITE)

    # Draw agents and their speech bubbles
    for i, agent in enumerate(agents):
        screen.blit(agent["sprite"], agent["pos"])
        if agent["show_bubble"]:
            draw_speech_bubble(agent["response"], agent["pos"], agent["sprite"])
            agent["bubble_timer"] -= 1
            if agent["bubble_timer"] <= 0:
                agent["show_bubble"] = False

        # Highlight the selected agent
        if i == selected_agent:
            pygame.draw.rect(screen, (255, 0, 0), (*agent["pos"], 32, 32), 2)

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
