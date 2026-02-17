"""Settings and configuration for mcs-orchestrator."""

import json
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 位于 mcs-orchestrator 项目根目录（与 pyproject.toml 同级）
_env_path = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings. 所有字段均可通过 .env 或环境变量覆盖，环境变量名为字段名大写（如 DIFY_BASE_URL）。"""

    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App（.env: APP_ENV, LOG_LEVEL）
    app_env: str = "dev"  # dev/staging/prod
    log_level: str = "INFO"

    # Database（.env: ORCHESTRATION_DB_DSN, MASTERDATA_DB_DSN, LISTENER_DB_DSN）
    # 支持分库：编排、主数据、监听各用独立数据库
    orchestration_db_dsn: str = "postgresql://user:password@localhost:5432/mcs_orchestrator"
    masterdata_db_dsn: str = "postgresql://user:password@localhost:5432/mcs_masterdata"
    listener_db_dsn: str = "postgresql://user:password@localhost:5432/mcs_listener"
    # 向后兼容：如果未设置 orchestration_db_dsn，使用 db_dsn
    db_dsn: str = ""  # 向后兼容，优先使用 orchestration_db_dsn

    # Dify（.env: DIFY_BASE_URL, DIFY_CONTRACT_APP_KEY, DIFY_ORDER_APP_KEY）
    dify_base_url: str = "https://api.dify.ai"
    dify_contract_app_key: str = ""
    dify_order_app_key: str = ""
    # Dify 专用接口配置（.env: DIFY_CONF，JSON 格式字符串）
    # 键名规则：{目录名}-{文件名}，如 sales_email-call_dify_contract
    # 值格式：{"url": "服务器域名", "path": "接口路径", "token": "访问ID"}
    dify_conf: str = "{}"

    # File Server（.env: FILE_SERVER_BASE_URL, FILE_SERVER_API_KEY）
    file_server_base_url: str = "http://localhost:8001"
    file_server_api_key: str = ""

    # SMTP（.env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS）
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # LangSmith（.env: LANGSMITH_API_KEY, LANGSMITH_TRACING_V2, LANGSMITH_PROJECT）
    langsmith_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "mcs-platform"

    # Security（.env: API_KEY, JWT_PUBLIC_KEY, ALLOWED_TENANTS）
    api_key: str = ""
    jwt_public_key: str = ""
    allowed_tenants: list[str] = []

    # Master Data Service（.env: MASTERDATA_API_URL, MASTERDATA_API_KEY）
    masterdata_api_url: str = "http://localhost:8002"
    masterdata_api_key: str = ""

    # Gateway（.env: ERP_BASE_URL, ERP_API_KEY, ERP_TENANT_ID）
    erp_base_url: str = "http://localhost:9000"
    erp_api_key: str = ""
    erp_tenant_id: str = ""
    # 向后兼容：gateway_url 已废弃，使用 erp_base_url
    gateway_url: str = ""  # 已废弃，保留以兼容旧代码

    # Listener（.env: ENABLED_LISTENERS, IMAP_*, ALIMAIL_*, WECHAT_*, POLL_INTERVAL_SECONDS）
    enabled_listeners: str = "email"  # 逗号分隔：email,wechat
    email_provider: str = "imap"  # imap/exchange/pop3/alimail
    # IMAP
    imap_host: str = "imap.example.com"
    imap_port: int = 993
    imap_user: str = ""
    imap_pass: str = ""
    # Exchange
    exchange_tenant_id: str = ""
    exchange_client_id: str = ""
    exchange_client_secret: str = ""
    # Alimail（阿里邮箱）
    alimail_client_id: str = ""
    alimail_client_secret: str = ""
    alimail_email_account: str = ""
    alimail_api_base_url: str = "https://alimail-cn.aliyuncs.com"
    alimail_folder_id: str = "2"
    alimail_poll_size: int = 100
    # WeChat Work（企业微信）
    wechat_corp_id: str = ""
    wechat_corp_secret: str = ""
    wechat_agent_id: str = ""
    wechat_webhook_url: str = ""
    # Polling
    poll_interval_seconds: int = 60
    # Channel access control (whitelist)
    # Format: JSON string mapping channel type to list of allowed sender IDs
    # Example: '{"email": ["user@example.com"], "wechat": ["user_id"]}'
    channel_allow_from: str = "{}"  # JSON string, empty dict means allow all

    # Cache（.env: REDIS_URL, CACHE_TTL_SECONDS）
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # Checkpoint（.env: CHECKPOINT_BACKEND）
    # redis = 使用 Redis（需 Redis Stack / RedisJSON 模块，否则会报 unknown command JSON.SET）
    # memory = 使用内存，无需 Redis JSON，适合本地/无 Redis Stack 环境（不持久化）
    checkpoint_backend: str = "redis"

    # Memory System (memU)（.env: MEMORY_ENABLED, MEMORY_DATABASE_PROVIDER, MEMORY_DATABASE_DSN, etc.）
    memory_enabled: bool = True  # Enable/disable memory system
    memory_database_provider: str = "inmemory"  # inmemory or postgres
    memory_database_dsn: str = ""  # PostgreSQL DSN if using postgres provider
    memory_llm_chat_model: str = "gpt-4o-mini"  # LLM model for memory extraction/retrieval
    memory_llm_embed_model: str = "text-embedding-3-small"  # Embedding model
    memory_llm_profiles: str = "{}"  # JSON string for custom LLM profiles

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

    def get_enabled_listeners(self) -> list[str]:
        """Get list of enabled listeners."""
        return [s.strip() for s in self.enabled_listeners.split(",") if s.strip()]

    def get_orchestration_db_dsn(self) -> str:
        """Get orchestration DB DSN, fallback to db_dsn for backward compatibility."""
        return self.orchestration_db_dsn or self.db_dsn or "postgresql://user:password@localhost:5432/mcs_orchestrator"

    def get_dify_conf(self) -> dict[str, dict[str, str]]:
        """Parse and return DIFY_CONF as a dictionary.
        
        Returns:
            dict[str, dict[str, str]]: Parsed Dify configuration, keyed by node name.
            Each value contains 'url', 'path', and 'token' keys.
        """
        if not self.dify_conf or not self.dify_conf.strip():
            return {}
        try:
            return json.loads(self.dify_conf)
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_dify_node_config(self, node_key: str) -> dict[str, str] | None:
        """Get Dify configuration for a specific node.
        
        Args:
            node_key: Node configuration key (e.g., 'sales_email-call_dify_contract')
            
        Returns:
            dict[str, str] | None: Node configuration with 'url', 'path', 'token' keys,
            or None if not found.
        """
        conf = self.get_dify_conf()
        return conf.get(node_key)

    def get_channel_allow_list(self, channel_type: str) -> list[str]:
        """Get allow list for a specific channel type.
        
        Args:
            channel_type: Channel type (e.g., 'email', 'wechat')
            
        Returns:
            list[str]: List of allowed sender IDs, empty list means allow all.
        """
        if not self.channel_allow_from or not self.channel_allow_from.strip():
            return []
        try:
            allow_dict = json.loads(self.channel_allow_from)
            return allow_dict.get(channel_type, [])
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def memory(self) -> "MemoryConfig":
        """Get memory configuration as a nested config object."""
        return MemoryConfig(
            enabled=self.memory_enabled,
            database_provider=self.memory_database_provider,
            database_dsn=self.memory_database_dsn,
            llm_chat_model=self.memory_llm_chat_model,
            llm_embed_model=self.memory_llm_embed_model,
            llm_profiles=self._parse_memory_llm_profiles(),
        )

    def _parse_memory_llm_profiles(self) -> dict[str, dict[str, Any]]:
        """Parse memory LLM profiles JSON string."""
        if not self.memory_llm_profiles or not self.memory_llm_profiles.strip():
            return {}
        try:
            return json.loads(self.memory_llm_profiles)
        except (json.JSONDecodeError, TypeError):
            return {}


class MemoryConfig:
    """Memory system configuration."""

    def __init__(
        self,
        enabled: bool = True,
        database_provider: str = "inmemory",
        database_dsn: str = "",
        llm_chat_model: str = "gpt-4o-mini",
        llm_embed_model: str = "text-embedding-3-small",
        llm_profiles: dict[str, dict[str, Any]] | None = None,
    ):
        """Initialize memory config."""
        self.enabled = enabled
        self.database_provider = database_provider
        self.database_dsn = database_dsn
        self.llm_chat_model = llm_chat_model
        self.llm_embed_model = llm_embed_model
        self.llm_profiles = llm_profiles or {}

