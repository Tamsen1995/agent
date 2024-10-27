import os
from agent_logic import AgentManager, OpenAILLM
from models import Agent

def list_agents(agent_manager):
    agents = agent_manager.get_all_agents()
    if not agents:
        print("No agents found.")
        return
    
    print("\nAvailable agents:")
    for agent in agents:
        print(f"ID: {agent.id}, Name: {agent.name}")

def create_new_agent(agent_manager):
    name = input("Enter agent name: ")
    agent_id = agent_manager.create_agent(name)  # Removed position parameters
    print(f"Created agent with ID: {agent_id}")
    return agent_id

def view_memories(agent_manager, agent_id):
    memories = agent_manager.cognitive_archive.list_all_memories_and_reflections(agent_id)
    if not memories:
        print("No memories found.")
        return
    
    print("\nMemories and Reflections:")
    for memory in memories:
        print(f"\n{memory}")

def main():
    agent_manager = AgentManager()
    current_agent_id = None

    while True:
        if current_agent_id is None:
            print("\nNo agent selected.")
        else:
            agent = agent_manager.get_agent(current_agent_id)  # Using new get_agent method
            if agent:
                print(f"\nCurrent agent: {agent.name} (ID: {current_agent_id})")
            else:
                print("\nSelected agent not found.")
                current_agent_id = None

        print("\nCommands:")
        print("1. List all agents")
        print("2. Create new agent")
        print("3. Select agent")
        print("4. Talk to current agent")
        print("5. View memories")
        print("6. Delete current agent")
        print("7. Exit")

        choice = input("\nEnter command (1-7): ")

        if choice == "1":
            list_agents(agent_manager)
        
        elif choice == "2":
            current_agent_id = create_new_agent(agent_manager)
        
        elif choice == "3":
            list_agents(agent_manager)
            agent_id = input("Enter agent ID to select: ")
            try:
                agent_id = int(agent_id)
                if agent_manager.get_agent(agent_id):
                    current_agent_id = agent_id
                else:
                    print("Agent not found.")
            except ValueError:
                print("Invalid agent ID")
        
        elif choice == "4":
            if current_agent_id is None:
                print("No agent selected.")
                continue
            
            user_input = input("\nEnter your message: ")
            response = agent_manager.talk(current_agent_id, user_input)
            print(f"\nAgent: {response}")
        
        elif choice == "5":
            if current_agent_id is None:
                print("No agent selected.")
                continue
            
            view_memories(agent_manager, current_agent_id)
        
        elif choice == "6":
            if current_agent_id is None:
                print("No agent selected.")
                continue
            
            if agent_manager.delete_agent(current_agent_id):
                print("Agent deleted successfully.")
                current_agent_id = None
            else:
                print("Failed to delete agent.")
        
        elif choice == "7":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
