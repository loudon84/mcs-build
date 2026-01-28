mcs-platform/
  services/
    mcs-orchestrator/          # Python: LangGraph + LangServe
    mcs-toolkit/               # Python: 可复用 tools（文件上传、相似度、dify client）
    mcs-erp-gateway/           # 可选：Python封装ERP（或由现有NestJS提供）
  gateway/
    nestjs-api/                # NestJS: 权限裁剪/统一鉴权/路由
  libs/
    contracts/                 # JSON Schema / OpenAPI / Pydantic models
  infra/
    docker/
    k8s/
  docs/
