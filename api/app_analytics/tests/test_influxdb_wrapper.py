from unittest import mock

import app_analytics
import pytest
from app_analytics.influxdb_wrapper import (
    InfluxDBWrapper,
    build_filter_string,
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_multiple_event_list_for_feature,
    get_multiple_event_list_for_organisation,
)
from django.conf import settings

# Given
org_id = 123
env_id = 1234
feature_id = 12345
feature_name = "test_feature"
influx_org = settings.INFLUXDB_ORG
read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"


def test_write(monkeypatch):
    # Given
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_write_api = mock.MagicMock()
    mock_influxdb_client.write_api.return_value = mock_write_api

    influxdb = InfluxDBWrapper("name")
    influxdb.add_data_point("field_name", "field_value")

    # When
    influxdb.write()

    # Then
    mock_write_api.write.assert_called()


def test_influx_db_query_when_get_events_then_query_api_called(monkeypatch):
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") |> range(start: -30d, stop: now()) '
            f'|> filter(fn:(r) => r._measurement == "api_call")         '
            f'|> filter(fn: (r) => r["_field"] == "request_count")         '
            f'|> filter(fn: (r) => r["organisation_id"] == "{org_id}") '
            f'|> drop(columns: ["organisation", "project", "project_id", "environment", '
            f'"environment_id"])'
            f"|> sum()"
        )
        .replace(" ", "")
        .replace("\n", "")
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_events_for_organisation(org_id)

    # Then
    mock_query_api.query.assert_called_once()

    call = mock_query_api.query.mock_calls[0]
    assert call[2]["org"] == influx_org
    assert call[2]["query"].replace(" ", "").replace("\n", "") == expected_query


def test_influx_db_query_when_get_events_list_then_query_api_called(monkeypatch):
    query = (
        f'from(bucket:"{read_bucket}") '
        f"|> range(start: -30d, stop: now()) "
        f'|> filter(fn:(r) => r._measurement == "api_call")                   '
        f'|> filter(fn: (r) => r["organisation_id"] == "{org_id}") '
        f'|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        f'"project_id", "environment", "environment_id", "host"])'
        f"|> aggregateWindow(every: 24h, fn: sum)"
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_event_list_for_organisation(org_id)

    # Then
    mock_query_api.query.assert_called_once_with(org=influx_org, query=query)


@pytest.mark.parametrize(
    "project_id, environment_id, expected_filters",
    (
        (
            None,
            None,
            ['r._measurement == "api_call"', f'r["organisation_id"] == "{org_id}"'],
        ),
        (
            1,
            None,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["project_id"] == "1"',
            ],
        ),
        (
            None,
            1,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["environment_id"] == "1"',
            ],
        ),
        (
            1,
            1,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["project_id"] == "1"',
                'r["environment_id"] == "1"',
            ],
        ),
    ),
)
def test_influx_db_query_when_get_multiple_events_for_organisation_then_query_api_called(
    monkeypatch, project_id, environment_id, expected_filters
):
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") '
            "|> range(start: -30d, stop: now()) "
            f"{build_filter_string(expected_filters)}"
            '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
            '"project_id", "environment", "environment_id", "host"]) '
            "|> aggregateWindow(every: 24h, fn: sum)"
        )
        .replace(" ", "")
        .replace("\n", "")
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_multiple_event_list_for_organisation(
        org_id, project_id=project_id, environment_id=environment_id
    )

    # Then
    mock_query_api.query.assert_called_once()

    call = mock_query_api.query.mock_calls[0]
    assert call[2]["org"] == influx_org
    assert call[2]["query"].replace(" ", "").replace("\n", "") == expected_query


def test_influx_db_query_when_get_multiple_events_for_feature_then_query_api_called(
    monkeypatch,
):
    query = (
        f'from(bucket:"{read_bucket}") '
        "|> range(start: -30d, stop: now()) "
        '|> filter(fn:(r) => r._measurement == "feature_evaluation")                   '
        '|> filter(fn: (r) => r["_field"] == "request_count")                   '
        f'|> filter(fn: (r) => r["environment_id"] == "{env_id}")                   '
        f'|> filter(fn: (r) => r["feature_id"] == "{feature_name}") '
        '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        '"project_id", "environment", "environment_id", "host"])'
        "|> aggregateWindow(every: 24h, fn: sum, createEmpty: false)                    "
        '|> yield(name: "sum")'
    )

    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    assert get_multiple_event_list_for_feature(env_id, feature_name) == []

    # Then
    mock_query_api.query.assert_called_once_with(org=influx_org, query=query)
