"""Create a batch endpoint + deployment over the scoring-input matrix (SDK v2).

Batch deployments use a scale-to-zero compute cluster: it bills nothing until a
job is submitted. Here the deployment scores the one-row-per-series scoring
matrix row-wise and appends the forecasts into a single output file.

Run (WSL / Python), from this folder:
    python deploy_batch.py --subscription <id> --resource-group <rg> --workspace <ws>

Not executed in the course build. Shapes verified against the current
azure-ai-ml v2 batch-deployment docs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from azure.ai.ml import MLClient, Input
from azure.ai.ml.constants import AssetTypes, BatchDeploymentOutputAction
from azure.ai.ml.entities import (
    AmlCompute,
    BatchEndpoint,
    BatchRetrySettings,
    CodeConfiguration,
    Environment,
    ModelBatchDeployment,
    ModelBatchDeploymentSettings,
)
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
ENDPOINT = "demand-forecast-batch"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--scoring-input", default="azureml:forecast_scoring_input@latest")
    args = p.parse_args()

    ml_client = MLClient(DefaultAzureCredential(), args.subscription,
                         args.resource_group, args.workspace)

    # Scale-to-zero cluster: no cost between jobs.
    if not any(c.name == "batch-cluster" for c in ml_client.compute.list()):
        ml_client.compute.begin_create_or_update(
            AmlCompute(name="batch-cluster", min_instances=0, max_instances=2,
                       size="STANDARD_DS3_v2")).result()

    ml_client.batch_endpoints.begin_create_or_update(BatchEndpoint(name=ENDPOINT)).result()

    # Deploy the version tagged stage=champion (fall back to latest).
    champ = next((m for m in ml_client.models.list(name="demand-forecaster")
                  if (m.tags or {}).get("stage") == "champion"), None)
    model = champ or ml_client.models.get(name="demand-forecaster", label="latest")

    deployment = ModelBatchDeployment(
        name="champion",
        endpoint_name=ENDPOINT,
        model=model,
        code_configuration=CodeConfiguration(code=str(HERE.parents[2] / "code"),
                                             scoring_script="../labs/lab-06-model-deployment/aml/batch_driver.py"),
        environment=Environment(image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04",
                                conda_file=str(HERE.parent.parent / "lab-05-model-training" / "aml" / "conda.yaml")),
        compute="batch-cluster",
        settings=ModelBatchDeploymentSettings(
            mini_batch_size=1,
            max_concurrency_per_instance=2,
            instance_count=1,
            output_action=BatchDeploymentOutputAction.APPEND_ROW,
            output_file_name="demand_forecast.csv",
            retry_settings=BatchRetrySettings(max_retries=2, timeout=300),
            logging_level="info",
        ),
    )
    ml_client.batch_deployments.begin_create_or_update(deployment).result()

    endpoint = ml_client.batch_endpoints.get(ENDPOINT)
    endpoint.defaults.deployment_name = deployment.name
    ml_client.batch_endpoints.begin_create_or_update(endpoint).result()

    job = ml_client.batch_endpoints.invoke(
        endpoint_name=ENDPOINT,
        input=Input(type=AssetTypes.URI_FILE, path=args.scoring_input),
    )
    print("Batch scoring job:", job.name)
    print("Delete the endpoint when done: az ml batch-endpoint delete -n", ENDPOINT, "--yes")


if __name__ == "__main__":
    main()
