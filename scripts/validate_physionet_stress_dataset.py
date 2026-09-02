from __future__ import annotations

import argparse

from positive_emotion_engine.physionet_stress_dataset import validation_report_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root")
    args = parser.parse_args()
    print(validation_report_json(args.dataset_root))


if __name__ == "__main__":
    main()
