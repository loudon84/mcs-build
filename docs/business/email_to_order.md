A. sales-email-agent（编排主控）

监听/拉取销售邮箱新邮件

联系人命中（contacts.email）

解析邮件正文关键字（“采购合同”）

校验是否有 PDF 附件

用 customers 做“附件名 ↔ 客户”相似度匹配

命中后：上传附件到文件服务器，拿 URL

调用 客户采购合同 Agent

成功后：调用 销售订单 Agent

最终：给销售发结果邮件（成功/失败）

B. 客户采购合同 Agent（合同识别） —— 使用 Dify

入参：customer_id / customer_num（你定义的客户编号）、文件URL

调用合同模板（提示词模板+字段约束）

调用 qwen2.5-vl 做 PDF 识别/抽取

出参：识别成功/失败 + 采购物料明细 JSON 包

C. 销售订单 Agent（ERP 下单） —— 使用 Dify

入参：customers、contacts 子集 + 采购明细 JSON

组装 ERP 销售订单新建接口报文

调 ERP 接口

出参：销售订单号 + 快速访问 URL

D. 手工维护 JSON（轻量主数据） —— API 接口处理

单文件 4 个对象（数组值）

作为 contacts / customers / companys / products 的“最小可用主数据”

