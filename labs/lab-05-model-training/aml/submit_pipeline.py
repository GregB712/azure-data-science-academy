"""Three-step Azure ML pipeline: validate -> train -> evaluate (SDK v2).

Each step is a command() node over the academy's code/ folder; the pipeline runs
on serverless compute. The data dependency between steps is what sequences them:
train references the validate output, evaluate references the train output.

Run (WSL / Python), from this folder:
    pip install azure-ai-ml azure-identity
    python submit_pipeline.py --subscription <id> --resource-group <rg> \
        --workspace <ws> --gold-uri "abfss://.../retail/gold/weekly_demand_features"

Not executed in the course build (no subscription). Shapes follow the current
azure-ai-ml v2 docs (@dsl.pipeline, command nodes, default_compute="serverless").
"""

from __future__ import annotations

import argparse
from pathlib import Path

from azure.ai.ml import Input, MLClient, Output, command, dsl
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
CODE_DIR = str(HERE.parents[2] / "code")
ENV = "azureml:demand-forecast-env@latest"


def _step(name: str, cmd: str, inputs: dict, outputs: dict):
    return command(name=name, code=CODE_DIR, command=cmd, inputs=inputs,
                   outputs=outputs, environment=ENV)


@dsl.pipeline(description="Validate the contract, backtest+train, then gate the model.")
def forecasting_pipeline(gold_input: Input, n_estimators: int = 300):
    validate = _step(
        "validate",
        "python -m forecasting.validate --data ${{inputs.gold}} --output ${{outputs.report}}",
        {"gold": gold_input},
        {"report": Output(type=AssetTypes.URI_FOLDER)},
    )
    train = _step(
        "train",
        # The echo references the validate output so train waits for it; the flag
        # list passed to the script is unchanged.
        'echo "validated at ${{inputs.report}}"; '
        "python -m forecasting.train --data ${{inputs.gold}} "
        "--output ${{outputs.model}} --n-estimators ${{inputs.n_estimators}}",
        {"gold": gold_input, "report": validate.outputs.report, "n_estimators": n_estimators},
        {"model": Output(type=AssetTypes.URI_FOLDER)},
    )
    evaluate = _step(
        "evaluate",
        "python -m forecasting.evaluate --metrics ${{inputs.model}}/metrics.json "
        "--output ${{outputs.decision}}",
        {"model": train.outputs.model},
        {"decision": Output(type=AssetTypes.URI_FOLDER)},
    )
    return {"model": train.outputs.model, "decision": evaluate.outputs.decision}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--gold-uri", required=True)
    args = p.parse_args()

    ml_client = MLClient(DefaultAzureCredential(), args.subscription,
                         args.resource_group, args.workspace)

    pipeline_job = forecasting_pipeline(
        gold_input=Input(type=AssetTypes.URI_FOLDER, path=args.gold_uri),
    )
    pipeline_job.settings.default_compute = "serverless"

    returned = ml_client.jobs.create_or_update(pipeline_job, experiment_name="retail-demand-forecasting")
    print("Submitted pipeline:", returned.name)
    print("Studio:", returned.studio_url)
    ml_client.jobs.stream(returned.name)


if __name__ == "__main__":
    main()
