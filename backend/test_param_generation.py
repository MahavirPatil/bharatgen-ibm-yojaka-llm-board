#!/usr/bin/env python3
"""
Minimal test script to verify Param-1-7B-MoE generation works.
Run from project root: python backend/test_param_generation.py
Or from backend: python test_param_generation.py (loads .env from parent)
"""
from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path

# Load .env from project root if available
root = Path(__file__).resolve().parent.parent
dotenv_path = root / ".env"
if dotenv_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    except ImportError:
        print("[WARN] python-dotenv not installed; using existing env vars.")
else:
    print(f"[WARN] No .env at {dotenv_path}")

def main() -> None:
    param_path = os.getenv("PARAM1_7B_MOE_PATH")
    if not param_path:
        print("FAIL: PARAM1_7B_MOE_PATH not set. Add it to .env or export it.")
        sys.exit(1)

    model_path = Path(param_path)
    if not model_path.exists():
        print(f"FAIL: Model path does not exist: {model_path}")
        sys.exit(1)

    print(f"Model path: {model_path}")
    print("Loading tokenizer and model (4-bit)...")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=False)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
    )
    device = next(model.parameters()).device
    print(f"Model loaded on {device}")

    # Minimal prompt — very short, low token count
    prompt = "Say hello in one word."
    max_new_tokens = 10
    gen_timeout_s = 90

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        return_token_type_ids=False,
        truncation=True,
        max_length=128,
    )
    input_len = inputs["input_ids"].shape[1]
    inputs = {k: v.to(device) for k, v in inputs.items()}

    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    eos_id = tokenizer.eos_token_id

    result_container: list = []  # [("ok", elapsed, text)] or [("err", exc)]

    def run_generate() -> None:
        try:
            t0 = time.time()
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    eos_token_id=eos_id,
                    use_cache=True,
                    pad_token_id=pad_id,
                    repetition_penalty=1.1,
                )
            elapsed = time.time() - t0
            gen_tokens = out[0][input_len:]
            text = tokenizer.decode(gen_tokens, skip_special_tokens=True)
            result_container.append(("ok", elapsed, text))
        except Exception as e:
            result_container.append(("err", e))

    th = threading.Thread(target=run_generate, daemon=True)
    th.start()
    th.join(timeout=gen_timeout_s)

    if not result_container:
        print(f"TIMEOUT: Generation did not finish within {gen_timeout_s}s. Model may be hanging.")
        sys.exit(1)

    tag, *rest = result_container[0]
    if tag == "err":
        exc = rest[0]
        print(f"FAIL: Generation raised: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    _, elapsed_s, text = result_container[0]
    print(f"PASS: Generation completed in {elapsed_s:.2f}s.")
    print(f"Output: {text!r}")
    sys.exit(0)


if __name__ == "__main__":
    main()
