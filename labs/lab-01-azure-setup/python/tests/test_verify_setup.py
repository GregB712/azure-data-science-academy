"""Offline tests for verify_setup.py using a fake ARM transport and a fake ADLS client.

These prove the script's logic and its use of the current SDK request/response
shapes for the control plane, without an Azure subscription. They do NOT prove
that your Azure environment is configured; run verify_setup.py for that.
Run from the lab folder:  python -m pytest python/tests
"""
import json
import sys
from pathlib import Path

import pytest
from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpTransport

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_setup as vs  # noqa: E402

SUB = "11111111-1111-1111-1111-111111111111"


class FakeCredential:
    def get_token(self, *scopes, **kwargs):
        return AccessToken("fake-token", 9_999_999_999)

    def get_token_info(self, *scopes, options=None):
        from azure.core.credentials import AccessTokenInfo
        return AccessTokenInfo("fake-token", 9_999_999_999)


class FakeArm(HttpTransport):
    def __init__(self, storage_props):
        self.storage_props = storage_props
        self.urls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def open(self):
        pass

    def close(self):
        pass

    def send(self, request, **kwargs):
        url = request.url
        self.urls.append(url)
        if "/subscriptions?" in url:
            body = {"value": [{"id": f"/subscriptions/{SUB}", "subscriptionId": SUB,
                               "displayName": "Lab", "state": "Enabled"}]}
        elif "/resourcegroups/rg-adsa-lab01?" in url.lower():
            body = {"id": "x", "name": "rg-adsa-lab01", "location": "westeurope",
                    "tags": {"project": "adsa", "owner": "me", "expires": "2026-12-01"},
                    "properties": {"provisioningState": "Succeeded"}}
        elif "storageAccounts/stadsatest" in url:
            assert "api-version=2023-05-01" in url
            body = {"id": "x", "name": "stadsatest", "location": "westeurope", "properties": self.storage_props}
        else:
            raise AssertionError(f"unexpected url {url}")
        return _http_response(request, 200, body)


def _http_response(request, status, body):
    import requests
    from azure.core.rest._requests_basic import RestRequestsTransportResponse
    r = requests.Response()
    r.status_code = status
    import io
    from urllib3 import HTTPResponse
    content = json.dumps(body).encode()
    r.raw = HTTPResponse(body=io.BytesIO(content), status=status, preload_content=False,
                         headers={"content-type": "application/json"})
    r.headers["content-type"] = "application/json"
    r.url = request.url
    resp = RestRequestsTransportResponse(request=request, internal_response=r)
    resp.read()
    return resp


@pytest.fixture
def patched(monkeypatch):
    import azure.identity
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.subscriptions import SubscriptionClient

    good = {"isHnsEnabled": True, "allowSharedKeyAccess": False, "allowBlobPublicAccess": False,
            "minimumTlsVersion": "TLS1_2"}
    transport = FakeArm(good)
    monkeypatch.setattr(azure.identity, "AzureCliCredential", FakeCredential)
    orig_rm, orig_sub = ResourceManagementClient.__init__, SubscriptionClient.__init__

    def rm_init(self, cred, sub, **kw):
        orig_rm(self, cred, sub, transport=transport, **kw)

    def sub_init(self, cred, **kw):
        orig_sub(self, cred, transport=transport, **kw)

    monkeypatch.setattr(ResourceManagementClient, "__init__", rm_init)
    monkeypatch.setattr(SubscriptionClient, "__init__", sub_init)
    vs.results.clear()
    return transport


def test_parse_env_file(tmp_path):
    p = tmp_path / "lab.env"
    p.write_text("# comment\nAZ_RESOURCE_GROUP=rg-x\nSTORAGE_PREFIX='st'\n\nBAD LINE\n")
    assert vs.parse_env_file(p) == {"AZ_RESOURCE_GROUP": "rg-x", "STORAGE_PREFIX": "st"}


def test_control_plane_all_pass(patched):
    out = vs.check_control_plane({"AZ_RESOURCE_GROUP": "rg-adsa-lab01", "STORAGE_ACCOUNT": "stadsatest"})
    assert out is not None and out[1] == "stadsatest"
    assert all(r.ok for r in vs.results), [r for r in vs.results if not r.ok]
    assert len(vs.results) == 8


def test_control_plane_flags_shared_key(patched):
    patched.storage_props = dict(patched.storage_props, allowSharedKeyAccess=True)
    vs.check_control_plane({"AZ_RESOURCE_GROUP": "rg-adsa-lab01", "STORAGE_ACCOUNT": "stadsatest"})
    failed = [r.name for r in vs.results if not r.ok]
    assert failed == ["shared key access disabled"]


def test_data_plane_with_fake_adls(monkeypatch):
    import azure.storage.filedatalake as dl

    store = {}

    class FileClient:
        def __init__(self, path):
            self.path = path

        def upload_data(self, data, overwrite):
            store[self.path] = data

        def download_file(self):
            data = store[self.path]
            return type("D", (), {"readall": lambda self: data})()

        def delete_file(self):
            del store[self.path]

    class FS:
        def get_file_client(self, path):
            return FileClient(path)

        def get_paths(self, path):
            return [type("P", (), {"name": k})() for k in store if k.startswith(path)]

    class Svc:
        def __init__(self, account_url, credential):
            assert account_url == "https://stadsatest.dfs.core.windows.net"

        def get_file_system_client(self, name):
            assert name == "bronze"
            return FS()

    monkeypatch.setattr(dl, "DataLakeServiceClient", Svc)
    vs.results.clear()
    vs.check_data_plane(FakeCredential(), "stadsatest")
    assert [r.ok for r in vs.results] == [True, True, True, True]
    assert store == {}
