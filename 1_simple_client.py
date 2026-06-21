#!/usr/bin/env python3
"""Simple LLM Chat Client for VS Code."""

import os
import httpx
import time

# Resolve API configurations
BASE_URL = (os.getenv("ANTHROPIC_BASE_URL") or "").strip()
if BASE_URL and not BASE_URL.endswith("/v1/chat/completions"):
    BASE_URL = BASE_URL.rstrip("/") + "/v1/chat/completions"

MODEL_NAME = os.getenv("CLAUDE_MODEL", "qwen3.5:9b").strip()

# Initialize conversation history
messages = [{"role": "system", "content": "You are helpful."}]


def main():
    if not BASE_URL:
        print("[!] Error: Set ANTHROPIC_BASE_URL environment variable.")
        return

    print(f"Connected to: {BASE_URL}")
    print(f"Using model: {MODEL_NAME}")
    print("Type your message and press Enter. Clear history with 'exit'.")

    with httpx.Client(timeout=60) as client:
        while True:
            try:
                # 1. Get user input
                prompt = input(f"\n👤 You ({MODEL_NAME}): ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ["exit", "quit"]:
                    break

                # 2. Append message (keep within limits)
                messages.append({"role": "user", "content": prompt[:4092]})

                # 3. Setup payload (Keep last 5 messages for context)
                payload = {
                    "model": MODEL_NAME,
                    "messages": messages[-5:],
                    "stream": False
                }
                
                print(f"\n🤖 {MODEL_NAME}: ", end="", flush=True)

                # 4. Send API Request
                response = client.post(BASE_URL, json=payload)
                response.raise_for_status()
                
                # 5. Parse JSON response
                result = response.json()
                
                if "choices" in result and result["choices"]:
                    assistant_message = result["choices"][0]["message"]["content"] or ""
                    print(assistant_message.strip())
                    
                    # Store assistant response in memory
                    messages.append({"role": "assistant", "content": assistant_message})
                else:
                    print("\n[!] Error: Unexpected response format from server.")

            except httpx.ReadTimeout:
                print("\n[!] Timeout waiting for response.")
            except httpx.HTTPStatusError as e:
                print(f"\n[!] HTTP Error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"\n[!] Error: {type(e).__name__}: {str(e)[:200]}")
            
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nChat session closed.")

