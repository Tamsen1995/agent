from networked_agent_manager import NetworkedAgentManager
from urllib.parse import urlparse
import sys
from discussion_viewer import view_live_discussion

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def start_group_discussion(agent_manager):
    agents = agent_manager.get_all_agents()
    if not agents:
        print("\nNo agents available. Please create some agents first.")
        return None
    
    # List available agents
    list_agents(agent_manager)
    
    # Get participating agents
    agent_ids = []
    print("\nSelect agents for discussion (minimum 2 required)")
    while True:
        agent_id = input("Enter agent ID to add to discussion (or 'done' to finish): ").strip()
        if agent_id.lower() == 'done':
            break
        try:
            agent_id = int(agent_id)
            if agent_manager.get_agent(agent_id):
                if agent_id not in agent_ids:
                    agent_ids.append(agent_id)
                    print(f"Added agent {agent_id} to discussion")
                else:
                    print("This agent is already in the discussion")
            else:
                print("Agent not found")
        except ValueError:
            print("Please enter a valid number")
    
    if len(agent_ids) < 2:
        print("\nError: Need at least 2 agents for a discussion")
        return None
    
    # Get and validate topic URL
    while True:
        topic_url = input("\nEnter URL for discussion topic: ").strip()
        if validate_url(topic_url):
            break
        print("Please enter a valid URL (e.g., https://example.com)")
    
    try:
        # Start discussion
        thread = agent_manager.start_topic_discussion(agent_ids, topic_url)
        print(f"\nDiscussion started with {len(agent_ids)} agents!")
        print("Agents are now conversing in the background")
        return thread
    except Exception as e:
        print(f"\nError starting discussion: {str(e)}")
        return None

def list_agents(agent_manager):
    agents = agent_manager.get_all_agents()
    if not agents:
        print("\nNo agents found")
        return
    
    print("\nAvailable agents:")
    print("-" * 30)
    for agent in agents:
        print(f"ID: {agent.id:<5} Name: {agent.name}")
    print("-" * 30)

def create_new_agent(agent_manager):
    while True:
        name = input("\nEnter agent name (or 'cancel' to go back): ").strip()
        if name.lower() == 'cancel':
            return
        if name:
            break
        print("Name cannot be empty")
    
    try:
        agent_id = agent_manager.create_agent(name)
        print(f"\nCreated agent '{name}' with ID: {agent_id}")
        return agent_id
    except Exception as e:
        print(f"\nError creating agent: {str(e)}")
        return None

def main():
    try:
        agent_manager = NetworkedAgentManager()
        current_discussion = None
        
        while True:
            print("\nNetworked Agent Discussion System")
            print("=" * 35)
            print("1. List all agents")
            print("2. Create new agent")
            print("3. Start group discussion")
            print("4. View live discussion")
            print("5. Stop discussion")
            print("6. Exit")
            print("=" * 35)
            
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == "1":
                list_agents(agent_manager)
            
            elif choice == "2":
                create_new_agent(agent_manager)
            
            elif choice == "3":
                if current_discussion and current_discussion.is_alive():
                    print("\nA discussion is already in progress. Please stop it first.")
                else:
                    current_discussion = start_group_discussion(agent_manager)
            
            elif choice == "4":
                if current_discussion and current_discussion.is_alive():
                    print("\nStarting live discussion viewer...")
                    print("(Press 'q' to return to menu)")
                    view_live_discussion(agent_manager)
                else:
                    print("\nNo active discussion")
            
            elif choice == "5":
                if current_discussion and current_discussion.is_alive():
                    try:
                        agent_manager.stop_discussion("discussion_1")
                        current_discussion.join(timeout=5)
                        print("\nDiscussion stopped successfully")
                        current_discussion = None
                    except Exception as e:
                        print(f"\nError stopping discussion: {str(e)}")
                else:
                    print("\nNo active discussion to stop")
            
            elif choice == "6":
                if current_discussion and current_discussion.is_alive():
                    print("\nStopping ongoing discussion...")
                    agent_manager.stop_discussion("discussion_1")
                    current_discussion.join(timeout=5)
                print("\nGoodbye!")
                break
            
            else:
                print("\nInvalid choice. Please enter a number between 1 and 6")

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        if current_discussion and current_discussion.is_alive():
            agent_manager.stop_discussion("discussion_1")
            current_discussion.join(timeout=5)
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
