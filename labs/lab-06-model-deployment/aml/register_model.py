"""Register the trained model after it passes the release gate, and mark it champion.

Release criteria first (Module 6 release lesson): read the training job's
metrics.json and apply forecasting.evaluate's gate. Only a model that beats the
naive baseline and meets the error/bias thresholds is registered. The newly
registered version is then given the MLflow `champion` alias so serving code can
load `models:/<name>@champion` without changing when a new version is promoted.

Run (WSL / Python), from this folder, after a training job:
    python register_model.py --subscription <id> --resource-group <rg> \
        --workspace <ws> --job-name <train_job_name>

Not executed in the course build (no subscription). SDK shapes follow the
current azure-ai-ml v2 docs; the alias call uses the MLflow client against the
workspace tracking URI.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))
from forecasting.evaluate import release_decision  # noqa: E402

MODEL_NAME = "demand-forecaster"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--job-name", required=True, help="Name of the completed training job")
    args = p.parse_args()

    ml_client = MLClient(DefaultAzureCredential(), args.subscription,
                         args.resource_group, args.workspace)

    # 1) Release gate: download metrics.json from the job output and apply the rule.
    with tempfile.TemporaryDirectory() as tmp:
        ml_client.jobs.download(name=args.job_name, download_path=tmp, output_name="model")
        metrics = json.loads(next(Path(tmp).rglob("metrics.json")).read_text())
    decision = release_decision(metrics["aggregate"])
    print(json.dumps(decision.__dict__, indent=2))
    if not decision.passed:
        raise SystemExit("Release blocked by the gate; not registering.")

    # 2) Register the MLflow model from the job output as a new version.
    model = Model(
        path=f"azureml://jobs/{args.job_name}/outputs/model",
        name=MODEL_NAME,
        type=AssetTypes.MLFLOW_MODEL,
        description=f"Demand forecaster from job {args.job_name}; WAPE={decision.wape:.3f}",
        tags={"wape": f"{decision.wape:.4f}", "mase": f"{decision.mase:.4f}", "stage": "candidate"},
    )
    registered = ml_client.models.create_or_update(model)
    print(f"Registered {registered.name}:{registered.version}")

    # 3) Promote to champion with a TAG. Azure ML resolves deployments by version
    #    or @latest (not by a custom alias), so champion/challenger is a tag
    #    convention here: deploy the version tagged stage=champion. Demote the
    #    previous champion so exactly one version holds the tag.
    for v in ml_client.models.list(name=MODEL_NAME):
        if v.version != registered.version and (v.tags or {}).get("stage") == "champion":
            v.tags["stage"] = "archived"
            ml_client.models.create_or_update(v)
    registered.tags["stage"] = "champion"
    ml_client.models.create_or_update(registered)
    print(f"{MODEL_NAME}:{registered.version} tagged stage=champion")


if __name__ == "__main__":
    main()
