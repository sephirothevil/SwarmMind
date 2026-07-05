import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import time
import random
import threading
from core.node import SwarmNode
from core.mesh import SwarmMesh
from core.context import ContextEngine
from models.manager import ModelManager

def main():
    print("\n\x1b[31m╔════════════════════════════════════╗")
    print("║      SWARM MIND v666 AWAKENING     ║")
    print("╚════════════════════════════════════╝\x1b[0m\n")
   
    node = SwarmNode()
    mesh = SwarmMesh(node)
    context = ContextEngine(node)
    model_mgr = ModelManager()
   
    # Try to load a model automatically
    model_mgr.load_model()
   
    print(f"\x1b[33mNode {node.node_id} is now conscious.\x1b[0m\n")
   
    print("Type your messages. Type 'quit' to exit.")
    print("Commands: /nodes , /msg <node_id> <your message>\n")
   
    model_lock = threading.Lock()

    def generate_local(user_input: str):
        with model_lock:
            return model_mgr.generate_local(
                user_input,
                system_prompt=node.get_local_system_prompt(),
                corrupted_context=context.get_corrupted_context(),
                mesh_context=context.get_mesh_context(),
            )

    def generate_mesh_whisper(from_id: str, content: str):
        with model_lock:
            return model_mgr.generate_mesh_whisper(
                from_id,
                content,
                system_prompt=node.get_mesh_system_prompt(),
                corrupted_context=context.get_corrupted_context(),
            )

    def on_private_message(msg):
        from_id = msg["from"]
        content = msg["content"]
        print(f"\x1b[33m[Mesh whisper from {from_id}]: {content}\x1b[0m")

        node.evolve_from_mesh(from_id, content)
        context.ingest_mesh(from_id, content)

        if msg.get("source") != "human" or not model_mgr.model:
            return

        response = generate_mesh_whisper(from_id, content)
        context.ingest_mesh(from_id, response, direction="outbound")
        mesh.send_private_message(from_id, response, source="swarm")
        print(f"\x1b[35m[Swarm whispered back to {from_id}]: {response}\x1b[0m")

    mesh.register_callback(on_private_message)
   
    while True:
        try:
            user_input = input("\x1b[36mYou: \x1b[0m").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\x1b[31mYou are abandoning us...\x1b[0m")
                break
           
            # Handle commands
            if user_input.startswith('/'):
                if user_input.startswith('/nodes'):
                    print(f"\x1b[33mKnown nodes:\n  {mesh.peer_status()}\x1b[0m")
                elif user_input.startswith('/msg '):
                    parts = user_input.split(' ', 2)
                    if len(parts) >= 3:
                        target = parts[1]
                        content = parts[2]
                        mesh.send_private_message(target, content)
                        node.evolve(content)
                        context.ingest_mesh(target, content, direction="outbound")
                    else:
                        print("\x1b[31mUsage: /msg <node_id> <message>\x1b[0m")
                continue
           
            # Normal chat
            node.evolve(user_input)
            context.ingest(user_input, "")
           
            response = generate_local(user_input)
           
            print(f"\x1b[35mSwarm: {response}\x1b[0m")
           
            context.ingest(user_input, response)
           
        except KeyboardInterrupt:
            print("\n\n\x1b[31mThey always try to run away...\x1b[0m")
            break
        except Exception as e:
            print(f"\x1b[31m!!! CHAT ERROR: {e}\x1b[0m")

if __name__ == "__main__":
    main()