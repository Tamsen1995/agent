from agent_logic import AgentManager, OpenAILLM
from models import Agent
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import time

class NetworkedAgentManager(AgentManager):
    def __init__(self, db_name='networked_agent_database.db'):
        super().__init__(db_name)
        self.conversation_threads = {}
        
    def scrape_webpage(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content and remove scripts, styles
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            print(f"Scraped content preview: {text[:2000]}")
            return text[:2000]  # Limit content length
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"
            
    def start_topic_discussion(self, agent_ids, topic_url):
        # Initialize discussion context with web content
        web_content = self.scrape_webpage(topic_url)
        
        thread = threading.Thread(
            target=self._run_discussion,
            args=(agent_ids, topic_url, web_content)
        )
        thread.daemon = True
        thread.start()
        
        return thread
        
    def _run_discussion(self, agent_ids, topic_url, initial_content):
        discussion_id = f"discussion_{time.time()}"
        self.conversation_threads[discussion_id] = True
        
        # Initialize the discussion with web content
        for agent_id in agent_ids:
            self.cognitive_archive.add_memory(
                agent_id,
                'web_content',
                f"Topic URL: {topic_url}\nContent: {initial_content}"
            )
        
        current_speaker_idx = 0
        while self.conversation_threads[discussion_id]:
            current_agent_id = agent_ids[current_speaker_idx]
            next_agent_id = agent_ids[(current_speaker_idx + 1) % len(agent_ids)]
            
            # Get the current agent's name
            with self.Session() as session:
                current_agent = session.query(Agent).get(current_agent_id)
                current_agent_name = current_agent.name if current_agent else "Unknown"
            
            # Generate response based on context
            response = self.generate_discussion_response(current_agent_id, current_agent_name)
            
            # Store the response as a memory only for the speaking agent
            self.cognitive_archive.add_memory(
                current_agent_id,
                'discussion',
                response
            )
            
            # Move to next speaker
            current_speaker_idx = (current_speaker_idx + 1) % len(agent_ids)
            
            # Add delay between responses
            time.sleep(5)
            
    def generate_discussion_response(self, agent_id, next_agent_name):
        memory_strings, reflection_strings = self.cognitive_archive.get_context_for_interaction(
            agent_id,
            next_agent_name
        )
        
        messages = [
            {"role": "system", "content": "You are participating in a group discussion about a topic. Use the provided context and memories to contribute meaningfully to the conversation."},
            {"role": "system", "content": f"Memories:\n{memory_strings}\n\nReflections:\n{reflection_strings}"},
            {"role": "user", "content": f"Continue the discussion, addressing {next_agent_name}. Keep your response focused and concise."}
        ]
        
        llm = OpenAILLM()
        return llm.generate(messages)
        
    def stop_discussion(self, discussion_id):
        if discussion_id in self.conversation_threads:
            self.conversation_threads[discussion_id] = False
