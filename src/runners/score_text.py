import argparse, yaml, time
from pathlib import Path

def save_run_card(out):
    run_dir = Path(f"runs/{out['run_id']}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_card.yaml").write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, 'r', encoding='utf-8'))

    t0 = time.time()
    out = {
        "run_id": f"{time.strftime('%Y-%m-%d_%H%M%S')}_{cfg.get('backend','na')}_seed{cfg.get('seed','na')}",
        "backend": cfg.get("backend"),
        "seed": cfg.get("seed"),
        "context_length": cfg.get("context_length", 2048),
        "model": None,
        "timings": {},
        "metrics": {},
        "memory": {},
        "tags": cfg.get("tags", []),
    }

    if cfg["backend"] == "cuda":
        from llama_cpp import Llama
        llm = Llama(model_path=cfg["model_path"], n_gpu_layers=-1)  # usa CUDA
        r = llm("Say 'pong' in one word:", max_tokens=4)
        out["model"] = cfg["model_path"]

    elif cfg["backend"] == "api":
        from openai import OpenAI
        client = OpenAI(base_url=cfg["base_url"], api_key="lm-studio")
        r = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": "Say 'pong' in one word:"}],
            temperature=0.1,
            max_tokens=4
        )
        out["model"] = cfg["model"]

    else:
        raise SystemExit("backend must be cuda|api")

    out["timings"]["wall_time_s"] = round(time.time() - t0, 3)
    save_run_card(out)
    print("Saved run_card:", out["run_id"])

if __name__ == "__main__":
    main()
