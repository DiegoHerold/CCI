from app.config import Settings, get_settings
from app.infrastructure.clients.audit_service_client import AuditServiceClient
from app.infrastructure.clients.base_client import BaseInternalClient
from app.infrastructure.clients.client_service_client import ClientServiceClient
from app.infrastructure.clients.conference_model_client import ConferenceModelClient
from app.infrastructure.clients.document_classification_client import DocumentClassificationClient
from app.infrastructure.clients.document_ingestion_client import DocumentIngestionClient
from app.infrastructure.clients.execution_control_client import ExecutionControlClient
from app.infrastructure.clients.identity_client import IdentityClient
from app.infrastructure.clients.log_service_client import LogServiceClient
from app.infrastructure.clients.report_service_client import ReportServiceClient
from app.infrastructure.clients.result_service_client import ResultServiceClient
from app.infrastructure.clients.rule_service_client import RuleServiceClient
from app.infrastructure.clients.schedule_service_client import ScheduleServiceClient
from app.infrastructure.clients.variable_registry_client import VariableRegistryClient


def settings_dependency() -> Settings:
    return get_settings()


def get_identity_client() -> IdentityClient:
    return IdentityClient(get_settings().identity_service_url)


def get_internal_clients() -> dict[str, BaseInternalClient]:
    settings = get_settings()
    clients: list[BaseInternalClient] = [
        IdentityClient(settings.identity_service_url),
        ClientServiceClient(settings.client_service_url),
        ConferenceModelClient(settings.conference_model_service_url),
        ScheduleServiceClient(settings.schedule_service_url),
        DocumentIngestionClient(settings.document_ingestion_service_url),
        DocumentClassificationClient(settings.document_classification_service_url),
        VariableRegistryClient(settings.variable_registry_service_url),
        RuleServiceClient(settings.rule_service_url),
        ExecutionControlClient(settings.execution_control_service_url),
        ResultServiceClient(settings.result_service_url),
        AuditServiceClient(settings.audit_service_url),
        ReportServiceClient(settings.report_service_url),
        LogServiceClient(settings.log_service_url),
    ]
    return {client.service_name: client for client in clients}
