import argparse, yaml
from pathlib import Path

def save_run_card(out):
    run_dir = Path(f"runs/{out['run_id']}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_card.yaml").write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--config", required=True)
args = ap.parse_args()
cfg = yaml.safe_load(open(args.config, 'r', encoding='utf-8'))

# texto de teste
Path("data/processed").mkdir(parents=True, exist_ok=True)
corpus_path = Path(cfg["task"]["input"])
if not corpus_path.exists():
    corpus_path.write_text("um texto simples de teste para calcular perplexidade.", encoding="utf-8")

# carrega LM
import kenlm
model = kenlm.Model(cfg["lm_path"])

# perplexidade simples por token
tokens = corpus_path.read_text(encoding="utf-8").split()
ppl = 10.0 ** (-model.score(" ".join(tokens)) / max(1, len(tokens)))

out = {
    "run_id": f"kenlm_{cfg['seed']}",
    "backend": "cpu-kenlm",
    "model": cfg["lm_path"],
    "metrics": {"ppl": float(f"{ppl:.4f}")},
    "tags": cfg.get("tags", [])
}
save_run_card(out)
print("PPL:", f"{ppl:.4f}")
