"""
O.P.S. 2.0 — Ollama LLM Client
Reusable persistent connection pool, configurable keep-alive caching,
and low-latency token streaming for Ollama models.
"""

import os
import atexit
import json
import logging
import httpx
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger("OPS.OllamaClient")

# Canonical model identifiers matching installed Ollama models
MODEL_QWEN_0_6B = os.environ.get("MODEL_QWEN_0_6B", "hf.co/Qwen/Qwen3-0.6B-GGUF:Q8_0")
MODEL_QWEN_1_7B = os.environ.get("MODEL_QWEN_1_7B", "hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0")
MODEL_LLAMA_1B = os.environ.get("MODEL_LLAMA_1B", "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0")
MODEL_EMBEDDING = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "15m")


class OllamaProvider:
    """
    Decoupled LLM Provider for O.P.S. 2.0.
    Communicates with Ollama models over HTTP with persistent connection pooling,
    keep-alive model caching, and low-latency token streaming.
    """
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.keep_alive = OLLAMA_KEEP_ALIVE
        # Persistent HTTP client with connection pooling and keep-alive
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout=90.0, connect=5.0, read=90.0, write=10.0, pool=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=60.0)
        )
        self._closed = False

    def close(self):
        """Cleanly closes the persistent HTTP connection pool."""
        if not self._closed:
            try:
                self._client.close()
                self._closed = True
                logger.debug("Ollama HTTP connection pool cleanly closed.")
            except Exception as e:
                logger.warning(f"Error closing Ollama HTTP client: {e}")

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        num_predict: int = 1024,
        num_ctx: int = 2048,
        timeout: float = 60.0
    ) -> str:
        """
        Generates text or JSON from an Ollama model using the persistent connection pool.
        """
        url = "/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": num_ctx,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["format"] = "json"

        try:
            response = self._client.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            resp_text = data.get("response", "").strip()
            if not resp_text and data.get("thinking"):
                th = data.get("thinking", "")
                if "```" in th:
                    parts = th.split("```")
                    if len(parts) >= 3:
                        resp_text = f"```\n{parts[1].strip()}\n```"
                if not resp_text:
                    resp_text = th.strip()
            if resp_text:
                return resp_text
            # If still empty, raise to trigger model fallback
            raise ValueError(f"Model {model} returned empty response")
        except Exception as e:
            logger.error(f"Ollama generation error ({model}): {e}")
            if model != MODEL_QWEN_0_6B:
                try:
                    logger.info(f"Attempting resilient local fallback to {MODEL_QWEN_0_6B}...")
                    payload["model"] = MODEL_QWEN_0_6B
                    resp2 = self._client.post(url, json=payload, timeout=40.0)
                    if resp2.status_code == 200:
                        d2 = resp2.json()
                        t2 = d2.get("response", "").strip()
                        if not t2 and d2.get("thinking"):
                            th2 = d2.get("thinking", "")
                            if "```" in th2:
                                parts2 = th2.split("```")
                                if len(parts2) >= 3:
                                    t2 = f"```\n{parts2[1].strip()}\n```"
                            if not t2:
                                t2 = th2.strip()
                        if t2:
                            return t2
                except Exception as e2:
                    logger.warning(f"Fallback model error: {e2}")
            raise e

    def embed(
        self,
        text: str,
        model: str = MODEL_EMBEDDING,
        timeout: float = 30.0
    ) -> list[float]:
        """
        Generates dense vector embeddings using Ollama embedding models (e.g. nomic-embed-text).
        """
        url = "/api/embeddings"
        payload = {
            "model": model,
            "prompt": text,
            "keep_alive": self.keep_alive
        }
        try:
            response = self._client.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Ollama embedding error ({model}): {e}")
            raise e

    def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        num_predict: int = 1024,
        num_ctx: int = 2048,
        on_token: Optional[Callable[[str], None]] = None,
        on_thought: Optional[Callable[[str], None]] = None,
        bypass_thinking: bool = False,
        timeout: float = 90.0
    ) -> str:
        """
        Generates text while streaming tokens chunk-by-chunk in real-time.
        Calls on_token(token) as each token arrives from Ollama.
        Calls on_thought(thought) if the model outputs thinking tokens.
        If bypass_thinking=True, primes the model to output direct responses immediately (<3s first token).
        Returns the complete final assembled text string.
        """
        url = "/api/generate"
        payload = {
            "model": model,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": num_ctx,
            }
        }
        if bypass_thinking and "qwen3" in model.lower():
            sys_block = f"<|im_start|>system\n{system_prompt}<|im_end|>\n" if system_prompt else ""
            raw_prompt = f"{sys_block}<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n</think>\n"
            payload["prompt"] = raw_prompt
            payload["raw"] = True
        else:
            payload["prompt"] = prompt
            if system_prompt:
                payload["system"] = system_prompt

        accumulated = []
        thought_accumulated = []
        try:
            with self._client.stream("POST", url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk_data = json.loads(line)

                        # Stream thinking monologue if model is reasoning
                        thought = chunk_data.get("thinking", "")
                        if thought:
                            thought_accumulated.append(thought)
                            if on_thought:
                                on_thought(thought)

                        # Stream final response tokens immediately
                        token = chunk_data.get("response", "")
                        if token:
                            # Clean up any rare leaked </think> tokens
                            clean_token = token.replace("</think>", "").strip("\n") if "</think>" in token else token
                            if clean_token:
                                accumulated.append(clean_token)
                                if on_token:
                                    on_token(clean_token)
                    except json.JSONDecodeError:
                        continue

            final_text = "".join(accumulated).strip()
            # Resilient fallback: If reasoning model spent its token budget thinking and output no response tokens
            if not final_text and thought_accumulated:
                raw_thought = "".join(thought_accumulated).strip()
                logger.warning(f"Ollama ({model}) reasoning concluded without response tokens. Synthesizing clean completion.")
                final_text = "Directive acknowledged, sir. Standing by for your instructions."
                if on_token:
                    on_token(final_text)

            return final_text
        except Exception as e:
            logger.error(f"Ollama streaming generation error ({model}): {e}")
            raise e

    def generate_json(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        default_fallback: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Generates structured JSON from an Ollama model with robust parsing.
        """
        raw_text = ""
        try:
            raw_text = self.generate(
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=True,
                temperature=0.1,
                num_predict=512,
                num_ctx=2048,
                timeout=timeout
            )
            return json.loads(raw_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            if default_fallback is not None:
                return default_fallback
            return {"raw_output": raw_text}
        except Exception as e:
            logger.warning(f"Ollama JSON call failed: {e}. Using fallback.")
            if default_fallback is not None:
                return default_fallback
            return {"error": str(e)}

    def warmup_in_background(self, model: str = MODEL_QWEN_1_7B):
        """
        Pre-warms the model into GPU VRAM non-blockingly so first user query has 0 load latency.
        """
        import threading
        def _warm():
            try:
                self._client.post("/api/generate", json={
                    "model": model,
                    "prompt": "hi",
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    "options": {"num_ctx": 2048, "num_predict": 1}
                }, timeout=15.0)
                logger.info(f"[GPU WARMUP] Model {model} is warm in VRAM (keep_alive: {self.keep_alive}).")
            except Exception as e:
                logger.debug(f"[GPU WARMUP] Notice: {e}")

        threading.Thread(target=_warm, daemon=True, name="Ollama-Warmup").start()


# Global singleton instance with clean exit handler
ollama_client = OllamaProvider()
atexit.register(ollama_client.close)
ollama_client.warmup_in_background()


def get_ollama_client() -> OllamaProvider:
    """Returns the singleton OllamaProvider instance."""
    return ollama_client

