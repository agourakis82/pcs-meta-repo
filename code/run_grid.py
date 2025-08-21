import itertools, pathlib, datetime, subprocess, sys

alphas = [0.1,0.2,0.3,0.4,0.5,0.6,0.8,1.0,1.5,2.0]
betas  = [0.005,0.01,0.015,0.02,0.025,0.03,0.04,0.05,0.06,0.08]

today = datetime.date.today().strftime("%Y%m%d")
csvfile = pathlib.Path(__file__).resolve().parent.parent / "paper_data" / f"run_{today}.csv"
csvfile.parent.mkdir(exist_ok=True)

# remove CSV corrompido, se existir
if csvfile.exists():
    csvfile.unlink()
    print("🗑️  CSV antigo removido:", csvfile.name)

for i, (a, b) in enumerate(itertools.product(alphas, betas), start=1):
    cmd = [
        sys.executable, "mc_sim.py",
        "--N", "10000", "--steps", "10000",
        "--alpha", str(a), "--beta", str(b),
        "--seed", "0", "--outcsv", str(csvfile)
    ]
    print(f"[{i:02d}/100]  α={a:>4}, β={b:>5} …", end=" ", flush=True)
    subprocess.run(cmd, cwd=pathlib.Path(__file__).parent, check=True)
    print("✔︎")

print("✅  Grid complete:", csvfile.relative_to(csvfile.parent.parent))