from app.domain.models import FailureType, RunStatus
from app.infrastructure.report_normalizer import ReportNormalizer


def test_normalizer_maps_raw_sih_like_json_to_domain_report():
    report = ReportNormalizer().normalize(
        {
            "run_id": "run-1",
            "workflow": "checkout-smoke",
            "environment": "staging",
            "version": "1.0.0",
            "started_at": "2026-05-06T10:00:00Z",
            "status": "failed",
            "stages": [
                {
                    "name": "create-order",
                    "status": "failed",
                    "duration_ms": 1000,
                    "http_status": 400,
                    "error_type": "contract_validation",
                }
            ],
        }
    )

    assert report.status == RunStatus.FAILED
    assert report.duration_ms == 1000
    assert report.stages[0].error_type == FailureType.CONTRACT_VALIDATION


def test_normalizer_maps_real_sih_pascal_case_report_to_domain_report():
    report = ReportNormalizer().normalize(
        {
            "ExecutionId": "01KQFGCBMCZGYHVTGEETZCJ2G5",
            "WorkflowName": "test-estimate-endpoint",
            "WorkflowVersion": "1.0",
            "ToolVersion": "1.7.20.278",
            "Environment": "local",
            "StartedAtUtc": "2026-04-30T15:33:37.550102+00:00",
            "DurationMs": 15764,
            "Result": "Ok",
            "Stages": [
                {
                    "StageName": "call-openai",
                    "Status": "Ok",
                    "DurationMs": 7148,
                    "HttpStatusCode": 200,
                    "RequestUri": "http://localhost:8000/api/v1/estimate",
                    "HttpMethod": "POST",
                    "ErrorMessage": None,
                }
            ],
        }
    )

    assert report.run_id == "01KQFGCBMCZGYHVTGEETZCJ2G5"
    assert report.workflow == "test-estimate-endpoint"
    assert report.environment == "local"
    assert report.status == RunStatus.PASSED
    assert report.tool_version == "1.7.20.278"
    assert report.stages[0].name == "call-openai"
    assert report.stages[0].http_status == 200
    assert report.stages[0].request_uri == "http://localhost:8000/api/v1/estimate"
