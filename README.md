# 🤖 Context-Clash: Neural Showdown

Context-Clash is a specialized local arena for AI-on-AI debates. It allows two large language models (running locally via Ollama) engage in a structured, competitive dialogue while giving the human observer the power to intervene as a "Heckler" or moderator.

## 🌟 Features

* **Model vs. Model:** Pit different local models (e.g., Llama3 vs. Mistral) against each other.
* **Persona Customization:** Define unique personalities for each combatant.
* **Pausable Debate Loop:** The battle pauses after each turn, allowing you to interject or steer the conversation.
* **Live Metrics:** Real-time tracking of token usage, generation speed (t/s), and context window saturation.
* **Transcript Export:** Save your neural showdowns as .txt files for later analysis.

## 🚀 Getting Started

### Prerequisites

* **Ollama:** Ensure [Ollama](https://ollama.com/) is installed and running.
* **Models:** Pull your preferred combatants:
  ```bash
  ollama pull llama3
  ollama pull mistral
  ```

### Installation

Install the package in editable mode to handle dependencies:
```bash
pip install -e .
```

### Running the Arena

Launch the application using the module entry point:
```bash
python -m context_clash
```

### Accessing the Interface

Once the server starts, open your browser and navigate to:
```text
http://localhost:8501
```
*Note: Streamlit usually opens this automatically, but you can manually navigate here if it does not.*

## 🎮 How to Play

1. **Select Models:** Choose your combatants from the sidebar.
2. **Set Personas:** Define the character of each AI (e.g., "A Grumpy Wizard" vs. "A Corporate Bot").
3. **Initiate:** Enter a seed topic to start the clash.
4. **Intervene:** The loop pauses after each response—use the **Heckler Mode** to interject or simply let the AIs continue.

## 📄 License

MIT License - feel free to use and modify for your own neural experiments.