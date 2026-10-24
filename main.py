import argparse

from src import run_pipeline
from src.pipeline import ESCENARIOS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimización multiobjetivo de rutas en Gran Canaria")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Hotel base (carpeta de data/). Por defecto, todos.")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad.")
    args = parser.parse_args()
    for escenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        print(f"\n=== Escenario: {escenario} ===")
        run_pipeline(escenario, seed=args.seed)
