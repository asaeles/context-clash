# 🤖 Context-Clash: Neural Showdown

Context-Clash is a specialized local arena for AI-on-AI debates. It solves the "role-collapse" hallucination common in multi-agent LLM systems by utilizing a strict **Perspective-Based History architecture**. Models engage in competitive dialogue via local Ollama instances, while the observer retains root control to intervene, moderate, or impersonate combatants.

## 🌟 Features

* **Perspective Wall Architecture:** Rebuilds conversational history asymmetrically per turn. Active model outputs map to the `assistant` role; opponent outputs map to the `user` role with explicit prefixing (e.g., `Rival says: ...`).
* **Model Agnosticism:** Assign different local models independently to Combatant A and Combatant B.
* **Dynamic Identity & Emoji Caching:** Define custom psychological personas. A secondary LLM generation executes a strict Unicode grapheme extraction to assign a representative emoji. Inputs are MD5-hashed and cached to eliminate redundant API calls and maintain UI state.
* **Advanced Generation Controls:** Enforce strict verbosity limits mapping to the engine's `num_predict` parameter, ranging from Concise (150 tokens) to Uncapped.
* **Live Saturation Metrics:** Real-time tracking of absolute token usage, generation speed (t/s), and context window saturation against a configurable 8192-token limit.
* **Tactical Intervention:** The execution loop pauses post-generation. Observers can inject neutral moderator prompts, force the next turn, or **Impersonate** a combatant to manually correct logical drift.
* **Transcript Export:** Export the complete, persona-tagged debate log as a `.txt` file upon reaching the designated turn limit.

## 🚀 Getting Started

### Prerequisites

* **Ollama:** Ensure [Ollama](https://ollama.com/) is installed and running locally.
* **Models:** Pull your preferred target models into the local registry:
  ```bash
  ollama pull llama3
  ollama pull mistral
  ```

### Installation

Install the package in editable mode to map dependencies:
```bash
pip install -e .
```

### Running the Arena

Launch the application using the module entry point:
```bash
python -m context_clash
```

### Accessing the Interface

Once the server initializes, open your browser and navigate to the default Streamlit port:
```text
http://localhost:8501
```

## 🎮 Arena Operations

1. **Select Models & Identities:** Choose combatants from the sidebar and define their strict character parameters.
2. **Configure Engine Limits:** Define total turn limits and output verbosity thresholds.
3. **Initiate:** Inject a seed topic to instantiate the global context and start the clash.
4. **Intervene:** Upon execution pause, utilize the Intervention Panel to:
   * **Mod Inject:** Issue a system-level directive.
   * **Let Speak:** Proceed to the next scheduled AI turn.
   * **Impersonate:** Write the upcoming response manually to steer the target model's future context.

## 📄 License

MIT License.
