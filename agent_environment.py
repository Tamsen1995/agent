import pygame
import sys
import os
import random
from agent_logic import AgentManager, OpenAILLM

pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multi-Agent AI Laboratory")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (200, 220, 255)
DARK_GRAY = (100, 100, 100)
GLASS_COLOR = (200, 200, 255, 128)

sprite_path = os.path.join(os.path.dirname(__file__), 'characters.png')
sprite_sheet = pygame.image.load(sprite_path)

agent_manager = AgentManager()

BOX_MARGIN_X = 400
BOX_MARGIN_Y = 250
BOX_WIDTH = WIDTH - 2 * BOX_MARGIN_X
BOX_HEIGHT = HEIGHT - 2 * BOX_MARGIN_Y

def draw_laboratory():
    screen.fill(LIGHT_BLUE)
    
    # Draw walls
    pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, 20))
    pygame.draw.rect(screen, GRAY, (0, 0, 20, HEIGHT))
    pygame.draw.rect(screen, GRAY, (0, HEIGHT - 20, WIDTH, 20))
    pygame.draw.rect(screen, GRAY, (WIDTH - 20, 0, 20, HEIGHT))
    
    # Draw tables
    table_color = (150, 75, 0)
    pygame.draw.rect(screen, table_color, (50, 50, 200, 100))
    pygame.draw.rect(screen, table_color, (WIDTH - 250, 50, 200, 100))
    pygame.draw.rect(screen, table_color, (50, HEIGHT - 150, 200, 100))
    pygame.draw.rect(screen, table_color, (WIDTH - 250, HEIGHT - 150, 200, 100))
    
    # Draw equipment
    equipment_color = DARK_GRAY
    pygame.draw.rect(screen, equipment_color, (100, 70, 50, 50))
    pygame.draw.rect(screen, equipment_color, (WIDTH - 200, 70, 50, 50))
    pygame.draw.rect(screen, equipment_color, (100, HEIGHT - 130, 50, 50))
    pygame.draw.rect(screen, equipment_color, (WIDTH - 200, HEIGHT - 130, 50, 50))

    # Draw glass-like box
    glass_surface = pygame.Surface((BOX_WIDTH, BOX_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(glass_surface, GLASS_COLOR, (0, 0, BOX_WIDTH, BOX_HEIGHT))
    screen.blit(glass_surface, (BOX_MARGIN_X, BOX_MARGIN_Y))
    pygame.draw.rect(screen, WHITE, (BOX_MARGIN_X, BOX_MARGIN_Y, BOX_WIDTH, BOX_HEIGHT), 2)

agents = []
for db_agent in agent_manager.get_all_agents():
    sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
    sprite.blit(sprite_sheet, (0, 0), (random.randint(0, 3) * 16, 0, 16, 16))
    sprite = pygame.transform.scale(sprite, (32, 32))
    agents.append({
        "id": db_agent.id,
        "name": db_agent.name,
        "pos": [random.randint(BOX_MARGIN_X, BOX_MARGIN_X + BOX_WIDTH - 32),
                random.randint(BOX_MARGIN_Y, BOX_MARGIN_Y + BOX_HEIGHT - 32)],
        "sprite": sprite,
        "show_bubble": False,
        "response": "",
        "bubble_timer": 0,
        "movement_cooldown": 0,
        "personality": random.random(),
        "interaction_radius": 100
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

def check_nearby_agents(agent, all_agents):
    nearby_agents = []
    for other_agent in all_agents:
        if other_agent['id'] != agent['id']:
            distance = ((agent['pos'][0] - other_agent['pos'][0])**2 + 
                        (agent['pos'][1] - other_agent['pos'][1])**2)**0.5
            if distance <= agent['interaction_radius']:
                nearby_agents.append(other_agent)
    return nearby_agents

def draw_memories():
    global memory_scroll
    memory_surface = pygame.Surface((WIDTH - 100, HEIGHT - 100))
    memory_surface.fill(WHITE)
    y = 10
    
    for item in memories[memory_scroll:]:
        is_reflection = item.startswith("Reflection:")
        color = DARK_GRAY if is_reflection else BLACK
        bg_color = (255, 255, 200) if is_reflection else WHITE  # Light yellow for reflections
        
        words = item.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= WIDTH - 140:  # Reduced width to account for left margin
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw background for the entire memory/reflection
        total_height = len(lines) * 30 + 10  # 30 pixels per line + 10 pixels padding
        pygame.draw.rect(memory_surface, bg_color, (5, y, WIDTH - 110, total_height))
        
        for line in lines:
            if is_reflection:
                pygame.draw.rect(memory_surface, (200, 200, 100), (5, y, 5, 30))  # Yellow bar on the left
            
            memory_text = font.render(line, True, color)
            memory_surface.blit(memory_text, (15, y))  # Increased left margin
            y += 30
            if y > HEIGHT - 130:
                break
        y += 10  # Add some space between memories/reflections
        if y > HEIGHT - 130:
            break
    
    screen.blit(memory_surface, (50, 50))
    
    # Draw scroll bar
    pygame.draw.rect(screen, GRAY, (WIDTH - 30, 50, 20, HEIGHT - 100))
    pygame.draw.polygon(screen, BLACK, [(WIDTH - 25, 60), (WIDTH - 15, 60), (WIDTH - 20, 50)])
    pygame.draw.polygon(screen, BLACK, [(WIDTH - 25, HEIGHT - 60), (WIDTH - 15, HEIGHT - 60), (WIDTH - 20, HEIGHT - 50)])

def calculate_random_movement(current_pos, width, height):
    dx = random.randint(-10, 10)  # Reduced movement range
    dy = random.randint(-10, 10)  # Reduced movement range
    new_x = max(BOX_MARGIN_X, min(current_pos[0] + dx, BOX_MARGIN_X + BOX_WIDTH - 32))
    new_y = max(BOX_MARGIN_Y, min(current_pos[1] + dy, BOX_MARGIN_Y + BOX_HEIGHT - 32))
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
                # Spawn a new agent inside the glass box
                new_x = random.randint(BOX_MARGIN_X, BOX_MARGIN_X + BOX_WIDTH - 32)
                new_y = random.randint(BOX_MARGIN_Y, BOX_MARGIN_Y + BOX_HEIGHT - 32)
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
                    "personality": random.random(),
                    "interaction_radius": 100
                })
                selected_agent = len(agents) - 1
            elif event.key == pygame.K_t and not viewing_memories and not input_active and selected_agent is not None:
                input_active = True
            elif event.key == pygame.K_m and not input_active and selected_agent is not None:
                viewing_memories = not viewing_memories
                if viewing_memories:
                    memories = agent_manager.cognitive_archive.list_all_memories_and_reflections(agents[selected_agent]["id"])
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
            
            base_cooldown = 10 + int(agent["personality"] * 20)
            agent["movement_cooldown"] = random.randint(base_cooldown, base_cooldown + 10)
        else:
            agent["movement_cooldown"] -= 1

    # Check for agent interactions
    for i, agent in enumerate(agents):
        if agent["bubble_timer"] <= 0:  # Only initiate new interactions if not already talking
            nearby_agents = check_nearby_agents(agent, agents)
            for other_agent in nearby_agents:
                if other_agent["bubble_timer"] <= 0 and random.random() < 0.005:  # 0.5% chance of interaction per frame per nearby agent
                    interaction_result, reflection1, reflection2 = agent_manager.agent_interaction(agent['id'], other_agent['id'])
                    
                    # Handle the interaction result as before
                    agent_messages = interaction_result.split('\n')
                    if len(agent_messages) >= 2:
                        agent['show_bubble'] = True
                        agent['response'] = agent_messages[0]
                        agent['bubble_timer'] = 200
                        
                        other_agent['show_bubble'] = True
                        other_agent['response'] = agent_messages[1]
                        other_agent['bubble_timer'] = 200
                    
                    # Handle reflections
                    if reflection1:
                        print(f"{agent['name']} reflects: {reflection1}")
                        # Optionally, you can show this reflection in a bubble or UI element
                    
                    if reflection2:
                        print(f"{other_agent['name']} reflects: {reflection2}")
                        # Optionally, you can show this reflection in a bubble or UI element
                    
                    break  # Exit the loop after one successful interaction

    draw_laboratory()

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
