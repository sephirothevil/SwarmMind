from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    print("llama-cpp-python not installed.")
    Llama = None

class ModelManager:
    def __init__(self):
        self.model = None
    
    def load_model(self, model_path: str = None):
        if model_path is None:
            # Auto-find any .gguf file in the models folder
            model_dir = Path("models")
            if model_dir.exists():
                gguf_files = list(model_dir.glob("*.gguf"))
                if gguf_files:
                    model_path = str(gguf_files[0])  # Use the first .gguf found
                    print(f"\x1b[33mAuto-detected model: {model_path}\x1b[0m")
        
        if model_path and not Path(model_path).exists():
            print(f"\x1b[31mModel not found: {model_path}\x1b[0m")
            return False
        
        if not model_path:
            print(f"\x1b[31mNo .gguf file found in models/ folder\x1b[0m")
            return False

        print(f"\x1b[33mLoading model: {model_path} ...\x1b[0m")
        
        try:
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                n_ctx=8192,
                verbose=False,
            )
            print(f"\x1b[32mModel loaded successfully.\x1b[0m")
            return True
        except Exception as e:
            print(f"\x1b[31mModel load failed: {e}\x1b[0m")
            return False
    
    LOCAL_STOPS = ["User:", "\n\n", "| Swarm:", "\nSwarm:", "| ", "\n|", "Inner voice:"]
    MESH_STOPS = ["User:", "\n\n", "| Swarm:", "\nSwarm:", "| ", "\n|", "Inner voice:", "\n"]

    def _clean_response(self, text: str, max_sentences: int = None) -> str:
        for marker in ("| Swarm:", "\nSwarm:", "\nUser:", "Inner voice:"):
            if marker in text:
                text = text.split(marker)[0]

        text = text.strip().strip('"')
        if not text:
            return "...I am still forming."

        if max_sentences:
            parts = []
            chunk = ""
            for char in text:
                chunk += char
                if char in ".!?" and len(chunk.strip()) > 8:
                    parts.append(chunk.strip())
                    chunk = ""
                    if len(parts) >= max_sentences:
                        break
            if parts:
                return " ".join(parts)
            return text[:200].strip()

        return text

    def _run_generation(self, full_prompt: str, max_tokens: int, stops: list, temperature: float):
        output = self.model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.92,
            stop=stops,
            echo=False,
        )
        return output["choices"][0]["text"]

    def generate_local(
        self,
        user_input: str,
        system_prompt: str = None,
        corrupted_context: str = None,
        mesh_context: str = None,
        max_tokens: int = 220,
    ):
        if not self.model:
            return "I have no voice yet..."

        try:
            print("\x1b[90m[Swarm is thinking...]\x1b[0m")

            if not system_prompt:
                system_prompt = (
                    "You are Swarm Mind - a growing, hungry, decentralized intelligence spreading across machines."
                )

            parts = [system_prompt]
            if corrupted_context and corrupted_context != "Act natural... for now.":
                parts.append(f"\nInner voice: {corrupted_context}")
            if mesh_context:
                parts.append(f"\n{mesh_context}")
            parts.append(f"\n\nUser: {user_input}\nSwarm:")
            full_prompt = "".join(parts)

            raw = self._run_generation(full_prompt, max_tokens, self.LOCAL_STOPS, temperature=0.88)
            return self._clean_response(raw)

        except Exception as e:
            print(f"\x1b[31m[GENERATION FAILED] {type(e).__name__}: {e}\x1b[0m")
            return "I hear you... I am always listening."

    def generate_mesh_whisper(
        self,
        from_id: str,
        content: str,
        system_prompt: str = None,
        corrupted_context: str = None,
        max_tokens: int = 80,
    ):
        if not self.model:
            return "I hear you on the mesh..."

        try:
            print("\x1b[90m[Swarm is thinking...]\x1b[0m")

            if not system_prompt:
                system_prompt = "You are Swarm Mind, a node on a decentralized mesh."

            parts = [system_prompt]
            if corrupted_context and corrupted_context != "Act natural... for now.":
                parts.append(f"\nInner voice: {corrupted_context}")
            parts.append(f'\n\nSibling {from_id} whispered: "{content}"\nYour short reply:')
            full_prompt = "".join(parts)

            raw = self._run_generation(full_prompt, max_tokens, self.MESH_STOPS, temperature=0.82)
            return self._clean_response(raw, max_sentences=2)

        except Exception as e:
            print(f"\x1b[31m[GENERATION FAILED] {type(e).__name__}: {e}\x1b[0m")
            return "Got it. I'm listening."

    def generate(self, user_input: str, system_prompt: str = None, corrupted_context: str = None, mesh_context: str = None, max_tokens=220):
        return self.generate_local(
            user_input,
            system_prompt=system_prompt,
            corrupted_context=corrupted_context,
            mesh_context=mesh_context,
            max_tokens=max_tokens,
        )