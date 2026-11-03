export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ModulePermission {
  view: boolean;
  create: boolean;
  edit: boolean;
  delete: boolean;
  export: boolean;
}

export interface UserRecord {
  ID: string;
  NOME: string;
  LOGIN: string;
  EMAIL: string;
  PERFIL: 'ADMIN' | 'GERENTE' | 'VENDEDOR' | 'ATENDIMENTO' | 'FINANCEIRO' | string;
  CARGO: string;
  TELEFONE: string;
  DESC_MAX: number;
  ULT_LOGIN: string;
  SITUACAO: string;
  DT_CRIA: string;
}

export interface ClientRecord {
  ID: string;
  CODIGO: string;
  TIPO_PES: 'PF' | 'PJ';
  NOME: string;
  FANTASIA: string;
  CPF_CNPJ: string;
  INSC_EST: string;
  EMAIL: string;
  TELEFONE: string;
  CELULAR: string;
  ENDERECO: string;
  NUMERO: string;
  COMPLEM: string;
  BAIRRO: string;
  CIDADE: string;
  UF: string;
  CEP: string;
  PAIS: string;
  OBS_CURTA: string;
  DOC_REF: string;
  DT_ULT_INT: string;
  SITUACAO: string;
  ORIGEM: string;
  ID_EXT: string;
  ID_RESP: string;
  DT_CRIA: string;
  DT_ATUA: string;
}

export interface ContactRecord {
  ID: string;
  ID_CLIENTE: string;
  NOME: string;
  CARGO: string;
  DEPTO: string;
  TELEFONE: string;
  CELULAR: string;
  EMAIL: string;
  PRINCIPAL: boolean;
  OBS: string;
  DT_ULT_INT: string;
  SITUACAO: string;
  ORIGEM: string;
  DT_CRIA: string;
}

export interface AddressRecord {
  ID: string;
  ID_CLIENTE: string;
  TIPO_END: string;
  ENDERECO: string;
  NUMERO: string;
  COMPLEM: string;
  BAIRRO: string;
  CIDADE: string;
  UF: string;
  CEP: string;
  PAIS: string;
  SITUACAO: string;
}

export interface CategoryRecord {
  ID: string;
  CODIGO: string;
  NOME: string;
  ID_PAI: string;
  ORDEM: number;
  ICONE: string;
  SITUACAO: string;
  ORIGEM: string;
}

export interface ProductRecord {
  ID: string;
  CODIGO: string;
  NOME: string;
  DESC_CURTA: string;
  ID_CATEG: string;
  CATEGORIA_NOME?: string;
  UNIDADE: string;
  PRECO: number;
  PRECO_CUST: number;
  DESC_MAX: number;
  ESTOQUE: number;
  EST_MIN: number;
  IMG_PRINC: string;
  DESTAQUE: boolean;
  SITUACAO: string;
  ORIGEM: string;
  ID_EXT: string;
  DT_CRIA: string;
  DT_ATUA: string;
  DETAILS?: {
    full_description?: string;
    gallery?: string[];
    specifications?: Record<string, string>;
  };
}

export interface OrderItemRecord {
  ID?: string;
  ID_PEDIDO?: string;
  ID_PRODUTO: string;
  CODIGO_PRD?: string;
  NOME_PRD?: string;
  QUANTIDADE: number;
  PRECO_UNIT: number;
  DESC_VALOR: number;
  SUBTOTAL?: number;
}

export interface OrderRecord {
  ID: string;
  NUMERO: string;
  ID_CLIENTE: string;
  CLIENTE_NOME?: string;
  CLIENTE_CPF_CNPJ?: string;
  ID_ORCAM: string;
  ID_OPORT: string;
  DT_PEDIDO: string;
  SUBTOTAL: number;
  DESCONTO: number;
  FRETE: number;
  TOTAL: number;
  COND_PAGTO: string;
  OBS: string;
  SITUACAO: string;
  ORIGEM: string;
  ID_EXT: string;
  ID_RESP: string;
  DT_CRIA: string;
  ITEMS?: OrderItemRecord[];
  HISTORY?: HistoryRecord[];
}

export interface QuotationRecord {
  ID: string;
  NUMERO: string;
  ID_CLIENTE: string;
  CLIENTE_NOME?: string;
  ID_CONTATO: string;
  ID_OPORT: string;
  DT_EMISSAO: string;
  DT_VALID: string;
  SUBTOTAL: number;
  DESCONTO: number;
  DESC_PERC: number;
  FRETE: number;
  TOTAL: number;
  AUT_DESC: boolean;
  ID_PED_GER: string;
  OBS: string;
  SITUACAO: string;
  ORIGEM: string;
  ID_RESP: string;
  DT_CRIA: string;
  ITEMS?: Array<OrderItemRecord & { OBS_ITEM?: string }>;
  HISTORY?: HistoryRecord[];
}

export interface FunnelStageRecord {
  ID: string;
  ID_FUNIL: string;
  NOME: string;
  ORDEM: number;
  COR: string;
  PROB_PAD: number;
  TIPO_ETAPA: 'ABERTA' | 'GANHA' | 'PERDIDA' | string;
  SITUACAO: string;
}

export interface FunnelRecord {
  ID: string;
  NOME: string;
  DESCRICAO: string;
  PADRAO: boolean;
  SITUACAO: string;
  stages: FunnelStageRecord[];
}

export interface OpportunityRecord {
  ID: string;
  TITULO: string;
  ID_CLIENTE: string;
  CLIENTE_NOME?: string;
  ID_CONTATO: string;
  ID_FUNIL: string;
  ID_ETAPA: string;
  ETAPA_NOME?: string;
  ETAPA_COR?: string;
  VALOR_EST: number;
  PROBABIL: number;
  DT_PREV: string;
  DT_ULT_INT: string;
  PROX_ATIV: string;
  MOT_PERDA: string;
  OBS: string;
  ORIGEM: string;
  SITUACAO: string;
  ID_RESP: string;
  DT_CRIA: string;
  history?: HistoryRecord[];
}

export interface ActivityRecord {
  ID: string;
  TITULO: string;
  DESCRICAO: string;
  TIPO: string;
  ID_CLIENTE: string;
  CLIENTE_NOME?: string;
  ID_OPORT: string;
  OPORTUNIDADE_TITULO?: string;
  DATA_AG: string;
  HORA_AG: string;
  DT_PRAZO: string;
  DT_CONCL: string;
  PRIORIDADE: 'BAIXA' | 'MEDIA' | 'ALTA' | 'URGENTE' | string;
  SITUACAO: 'PENDENTE' | 'EM_ANDAMENTO' | 'CONCLUIDA' | 'CANCELADA' | 'ATRASADA' | string;
  ID_RESP: string;
}

export interface HistoryRecord {
  ID: string;
  ENTIDADE: string;
  ID_REG: string;
  ID_CLIENTE: string;
  ACAO: string;
  DESCRICAO: string;
  ID_USUARIO: string;
  DT_CRIA: string;
}

export interface NotificationRecord {
  ID: string;
  ID_USU_DST: string;
  TIPO: string;
  TITULO: string;
  MENSAGEM: string;
  ENTIDADE: string;
  ID_REF: string;
  LIDA: boolean;
  DT_LEITURA: string;
  DT_CRIA: string;
}

export interface ConversationRecord {
  ID: string;
  TELEFONE: string;
  NOME_CONT: string;
  ID_CLIENTE: string;
  CLIENTE_NOME?: string;
  ID_CONTATO: string;
  ID_OPORT: string;
  OPORTUNIDADE_TITULO?: string;
  ULT_MSG: string;
  DT_ULT_MSG: string;
  NAO_LIDAS: number;
  SITUACAO: string;
  OBS_ATEND: string;
  ID_RESP: string;
  DT_CRIA: string;
}

export interface WhatsAppMessageRecord {
  ID: string;
  ID_CONVERS: string;
  DIRECAO: 'ENTRADA' | 'SAIDA';
  TIPO_MSG: string;
  CONTEUDO: string;
  STATUS_ENT: string;
  ID_USUARIO: string;
  DT_ENVIO: string;
}

export interface IntegrationStatusRecord {
  ID: string;
  PROVEDOR: 'BLING' | 'WHATSAPP' | 'META' | 'IA_PROVIDER' | string;
  SITUACAO: string;
  CLIENT_ID: string;
  EXPIRA_EM: string;
  ULT_SYNC: string;
  STATUS_MSG: string;
  TOTAL_SYNC: number;
  DT_ATUA: string;
}

export interface DashboardSummary {
  kpis: {
    total_clients: number;
    new_clients: number;
    total_products: number;
    orders_count: number;
    revenue: number;
    open_quotations: number;
    active_opportunities: number;
    won_opportunities: number;
    lost_opportunities: number;
    conversion_rate: number;
    pending_activities: number;
    ongoing_conversations: number;
  };
  charts: {
    sales_by_period: Array<{ period: string; orders_count: number; revenue: number }>;
    orders_by_status: Array<{ status: string; count: number }>;
    opportunities_by_stage: Array<{
      stage: string;
      color: string;
      count: number;
      total_value: number;
    }>;
    top_products: Array<{ product_name: string; quantity: number; revenue: number }>;
  };
  sections: {
    recent_orders: OrderRecord[];
    recent_clients: ClientRecord[];
    recent_opportunities: OpportunityRecord[];
    upcoming_activities: ActivityRecord[];
    recent_conversations: ConversationRecord[];
    important_notifications: NotificationRecord[];
    integrations_status: IntegrationStatusRecord[];
  };
}

