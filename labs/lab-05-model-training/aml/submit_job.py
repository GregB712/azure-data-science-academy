"""Submit the demand-forecast training as an Azure ML command job (SDK v2).

Equivalent to `az ml job create -f train-job.yml`, but in Python so you can
register the environment and data asset first and stream the job. Auth is via
your `az login`; no secrets.

Run (WSL / Python), from this folder, with azure-ai-ml installed:
    pip install azure-ai-ml azure-identity
    python submit_job.py \
        --subscription <sub-id> --resource-group <rg> --workspace <ws> \
        --gold-uri "abfss://lakehouse@<account>.dfs.core.windows.net/retail/gold/weekly_demand_features"

Not executed in the course build (no subscription). The SDK calls follow the
current azure-ai-ml v2 shapes verified against Microsoft Learn.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from azure.ai.ml import MLClient, command
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data, Environment
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parents[2] / "code"   # academy code/ folder (holds the forecasting package)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--gold-uri", required=True, help="abfss:// path of gold/weekly_demand_features")
    p.add_argument("--n-estimators", type=int, default=300)
    args = p.parse_args()

    ml_client = MLClient(DefaultAzureCredential(), args.subscription,
                         args.resource_group, args.workspace)

    # 1) Register the custom environment (built once, cached in the workspace ACR).
    env = Environment(
        name="demand-forecast-env",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04",
        conda_file=str(HERE / "conda.yaml"),
        description="LightGBM + delta-rs + MLflow for demand forecasting.",
    )
    env = ml_client.environments.create_or_update(env)

    # 2) Register the Gold table as a versioned uri_folder data asset.
    gold = Data(
        name="weekly_demand_features",
        type=AssetTypes.URI_FOLDER,
        path=args.gold_uri,
        description="Gold weekly demand features (Delta), contract v1.",
    )
    gold = ml_client.data.create_or_update(gold)

    # 3) Build and submit the command job. No `compute=` -> serverless compute.
    from azure.ai.ml import Input, Output

    job = command(
        code=str(CODE_DIR),
        command=("python -m forecasting.train --data ${{inputs.gold}} "
                 "--output ${{outputs.model}} --n-estimators ${{inputs.n_estimators}}"),
        inputs={
            "gold": Input(type=AssetTypes.URI_FOLDER, path=f"{gold.name}:{gold.version}"),
            "n_estimators": args.n_estimators,
        },
        outputs={"model": Output(type=AssetTypes.URI_FOLDER)},
        environment=f"{env.name}:{env.version}",
        experiment_name="retail-demand-forecasting",
        display_name="demand-forecast-train",
    )

    returned = ml_client.jobs.create_or_update(job)
    print("Submitted:", returned.name)
    print("Studio:", returned.studio_url)
    ml_client.jobs.stream(returned.name)   # tails logs until the job finishes


if __name__ == "__main__":
    main()
