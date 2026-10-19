"""Create a managed online endpoint with a blue/green deployment (SDK v2).

Online endpoints bill PER INSTANCE while deployed, even at zero traffic, so this
is the one part of the course that keeps costing money until you delete it. The
script creates a 'blue' deployment at 100% traffic, then shows the blue/green
shift pattern.

Auth modes: key (shared key), aml_token (Azure ML token), aad_token (Microsoft
Entra token, preview). We use key for the lab.

Run (WSL / Python), from this folder:
    python deploy_online.py --subscription <id> --resource-group <rg> --workspace <ws>

Not executed in the course build. Shapes verified against the current
azure-ai-ml v2 online-endpoint docs. REMEMBER to delete the endpoint afterwards.
"""

from __future__ import annotations

import argparse
import datetime

from azure.ai.ml import MLClient
from azure.ai.ml.entities import ManagedOnlineDeployment, ManagedOnlineEndpoint
from azure.identity import DefaultAzureCredential


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--instance-type", default="Standard_DS3_v2")
    args = p.parse_args()

    ml_client = MLClient(DefaultAzureCredential(), args.subscription,
                         args.resource_group, args.workspace)

    name = "demand-forecast-" + datetime.datetime.now().strftime("%m%d%H%M")
    endpoint = ManagedOnlineEndpoint(name=name, auth_mode="key",
                                     description="Real-time demand scoring")
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()

    # No-code deployment of the registered MLflow model (version tagged champion).
    champ = next((m for m in ml_client.models.list(name="demand-forecaster")
                  if (m.tags or {}).get("stage") == "champion"), None)
    model = champ or ml_client.models.get(name="demand-forecaster", label="latest")
    blue = ManagedOnlineDeployment(
        name="blue",
        endpoint_name=name,
        model=model,
        instance_type=args.instance_type,
        instance_count=1,
    )
    ml_client.online_deployments.begin_create_or_update(blue).result()  # ~8-10 min

    endpoint.traffic = {"blue": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()

    print(f"Endpoint '{name}' live; blue=100%.")
    print("Blue/green: deploy 'green' with the challenger model, then shift traffic:")
    print(f"  az ml online-endpoint update --name {name} --traffic \"blue=90 green=10\"")
    print(f"DELETE WHEN DONE (it bills while live):  az ml online-endpoint delete -n {name} --yes")


if __name__ == "__main__":
    main()
