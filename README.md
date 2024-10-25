# AI Agent Game

This project is an interactive game featuring an AI agent powered by OpenAI's GPT model. The game uses Pygame for visualization and allows users to interact with an AI agent in a graphical environment.

## Features

- Graphical interface using Pygame
- AI agent powered by OpenAI's GPT model
- Character movement using arrow keys
- Interaction with the AI agent by pressing 'T'
- Speech bubble display for AI responses
- Agent reflection and memory system

## Requirements

- Python 3.x
- Pygame
- OpenAI API key

## Installation

1. Clone this repository:

   ```
   git clone
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   Create a `.env` file in the project root and add your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the game:

```
python agent.py
```

- Use arrow keys to move the character
- Press 'T' to talk to the AI agent
- Press 'ESC' to quit the game

## Code Structure

- `agent.py`: Main game file containing Pygame setup, AI agent logic, and game loop
- `characters.png`: Sprite sheet for the game character

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
