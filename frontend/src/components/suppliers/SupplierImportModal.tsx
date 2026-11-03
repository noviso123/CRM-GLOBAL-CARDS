import React, { useState, useEffect } from 'react';
import {
  X,
  Search,
  Link as LinkIcon,
  Download,
  CheckCircle,
  ExternalLink,
  Layers,
  DollarSign,
  PackageCheck,
  AlertCircle,
  Sparkles,
  RefreshCw,
  Box,
  Truck,
  ArrowRight,
  ShieldCheck,
  Calculator,
} from 'lucide-react';
import { apiRequest } from '../../services/api';

export interface SupplierPartner {
  id: string;
  nome: string;
  dominio: string;
  url_base: string;
  badge_color: string;
  descricao: string;
  especialidades: string[];
  lotes_padrao: number[];
}

export interface SupplierProduct {
  id: string;
  fornecedor_id: string;
  fornecedor_nome: string;
  nome: string;
  sku_sugerido?: string;
  categoria: string;
  descricao: string;
  imagem: string;
  galeria?: string[];
  preco_custo_unit: number;
  preco_venda_sugerido_unit: number;
  lotes_disponiveis: number[];
  lote_padrao?: number;
  preco_custo_lote?: number;
  preco_venda_lote?: number;
  especificacoes: Record<string, string>;
  url_origem: string;
}

interface SupplierImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess?: () => void;
}

export const SupplierImportModal: React.FC<SupplierImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'catalog' | 'url'>('catalog');
  const [partners, setPartners] = useState<SupplierPartner[]>([]);
  const [selectedPartnerId, setSelectedPartnerId] = useState<string>('ALL');
  const [catalogItems, setCatalogItems] = useState<SupplierProduct[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [extractingUrl, setExtractingUrl] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Produto selecionado para configuração e importação
  const [selectedProduct, setSelectedProduct] = useState<SupplierProduct | null>(null);
  const [configMode, setConfigMode] = useState<'UN' | 'LOTE'>('UN');
  const [batchSize, setBatchSize] = useState<number>(50);
  const [costPrice, setCostPrice] = useState<number>(0);
  const [profitMargin, setProfitMargin] = useState<number>(120); // 120%
  const [salePrice, setSalePrice] = useState<number>(0);
  const [initialStock, setInitialStock] = useState<number>(50);
  const [minStock, setMinStock] = useState<number>(10);
  const [customSku, setCustomSku] = useState<string>('');
  const [customCategory, setCustomCategory] = useState<string>('Crachás & Identificação');

  // Estado de submissão
  const [importing, setImporting] = useState(false);
  const [importSuccessData, setImportSuccessData] = useState<any | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPartners();
      loadCatalog();
    } else {
      resetState();
    }
  }, [isOpen]);

  const resetState = () => {
    setSelectedProduct(null);
    setImportSuccessData(null);
    setErrorMsg(null);
    setUrlInput('');
  };

  const loadPartners = async () => {
    try {
      const data = await apiRequest<SupplierPartner[]>('/suppliers/partners');
      setPartners(data);
    } catch (err: any) {
      console.error('Erro ao carregar parceiros fornecedores:', err);
    }
  };

  const loadCatalog = async (query = '', partner = selectedPartnerId) => {
    setLoadingCatalog(true);
    setErrorMsg(null);
    try {
      const params = new URLSearchParams();
      if (query.trim()) params.append('q', query.trim());
      if (partner && partner !== 'ALL') params.append('supplier', partner);
      const data = await apiRequest<SupplierProduct[]>(`/suppliers/catalog?${params.toString()}`);
      setCatalogItems(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Falha ao buscar catálogo dos fornecedores.');
    } finally {
      setLoadingCatalog(false);
    }
  };

  const handlePartnerFilter = (partnerId: string) => {
    setSelectedPartnerId(partnerId);
    loadCatalog(searchQuery, partnerId);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCatalog(searchQuery, selectedPartnerId);
  };

  const handleExtractUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setExtractingUrl(true);
    setErrorMsg(null);
    try {
      const data = await apiRequest<any>('/suppliers/extract-url', {
        method: 'POST',
        body: JSON.stringify({ url: urlInput.trim() }),
      });

      // Transforma para o formato de produto selecionado
      const prod: SupplierProduct = {
        id: `EXT-${Date.now()}`,
        fornecedor_id: data.fornecedor_id || 'ATUAL_CARD',
        fornecedor_nome: data.fornecedor_nome || 'Fornecedor Gráfico',
        nome: data.nome || 'Produto Gráfico Extraído',
        sku_sugerido: `IMP-${data.fornecedor_id?.substring(0, 3)}-${Math.floor(100 + Math.random() * 900)}`,
        categoria: 'Crachás & Identificação',
        descricao: data.descricao || '',
        imagem: data.imagem || 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f',
        galeria: data.galeria || [],
        preco_custo_unit: data.preco_custo_estimado || 4.5,
        preco_venda_sugerido_unit: data.preco_venda_sugerido || 9.9,
        lotes_disponiveis: data.lotes_disponiveis || [25, 50, 100, 250, 500, 1000],
        lote_padrao: 50,
        especificacoes: data.especificacoes || {
          Origem: 'Importação por Link Web Direto',
          Fornecedor: data.fornecedor_nome,
        },
        url_origem: data.url_origem || urlInput,
      };

      openConfigDrawer(prod);
    } catch (err: any) {
      setErrorMsg(err.message || 'Erro ao extrair metadados da URL.');
    } finally {
      setExtractingUrl(false);
    }
  };

  const openConfigDrawer = (product: SupplierProduct) => {
    setSelectedProduct(product);
    setImportSuccessData(null);
    setErrorMsg(null);

    // Valores iniciais calculados
    const isLote = product.lote_padrao && product.lote_padrao > 1;
    const defaultBatch = product.lote_padrao || (product.lotes_disponiveis[0] || 50);
    setBatchSize(defaultBatch);

    const initialCost = isLote && product.preco_custo_lote
      ? product.preco_custo_lote
      : product.preco_custo_unit;
    setCostPrice(initialCost);

    const initialSale = isLote && product.preco_venda_lote
      ? product.preco_venda_lote
      : product.preco_venda_sugerido_unit;
    setSalePrice(initialSale);

    const calculatedMargin = initialCost > 0
      ? Math.round(((initialSale - initialCost) / initialCost) * 100)
      : 120;
    setProfitMargin(calculatedMargin);

    setConfigMode(isLote ? 'LOTE' : 'UN');
    setInitialStock(isLote ? 5 : 50);
    setMinStock(isLote ? 1 : 10);
    setCustomSku(product.sku_sugerido || `PRD-${Date.now().toString().slice(-6)}`);
    setCustomCategory(product.categoria || 'Crachás & Identificação');
  };

  const handleModeChange = (mode: 'UN' | 'LOTE') => {
    setConfigMode(mode);
    if (!selectedProduct) return;
    if (mode === 'UN') {
      const c = selectedProduct.preco_custo_unit || 4.5;
      const s = selectedProduct.preco_venda_sugerido_unit || Number((c * (1 + profitMargin / 100)).toFixed(2));
      setCostPrice(c);
      setSalePrice(s);
      setInitialStock(50);
      setMinStock(10);
    } else {
      const b = batchSize || 50;
      const c = selectedProduct.preco_custo_lote || Number((selectedProduct.preco_custo_unit * b).toFixed(2));
      const s = selectedProduct.preco_venda_lote || Number((c * (1 + profitMargin / 100)).toFixed(2));
      setCostPrice(c);
      setSalePrice(s);
      setInitialStock(5);
      setMinStock(1);
    }
  };

  const handleBatchChange = (newBatch: number) => {
    setBatchSize(newBatch);
    if (configMode === 'LOTE' && selectedProduct) {
      const unitCost = selectedProduct.preco_custo_unit || (costPrice / batchSize);
      const newCost = Number((unitCost * newBatch).toFixed(2));
      setCostPrice(newCost);
      const newSale = Number((newCost * (1 + profitMargin / 100)).toFixed(2));
      setSalePrice(newSale);
    }
  };

  const handleMarginChange = (newMargin: number) => {
    setProfitMargin(newMargin);
    if (costPrice > 0) {
      const newSale = Number((costPrice * (1 + newMargin / 100)).toFixed(2));
      setSalePrice(newSale);
    }
  };

  const handleSalePriceChange = (newSale: number) => {
    setSalePrice(newSale);
    if (costPrice > 0 && newSale > costPrice) {
      const m = Math.round(((newSale - costPrice) / costPrice) * 100);
      setProfitMargin(m);
    }
  };

  const handleConfirmImport = async () => {
    if (!selectedProduct) return;
    setImporting(true);
    setErrorMsg(null);
    try {
      const payload = {
        fornecedor_id: selectedProduct.fornecedor_id,
        fornecedor_nome: selectedProduct.fornecedor_nome,
        nome: selectedProduct.nome,
        sku: customSku.trim() || selectedProduct.sku_sugerido,
        categoria: customCategory,
        modo_venda: configMode,
        lote_quantidade: configMode === 'LOTE' ? batchSize : 1,
        preco_custo: costPrice,
        preco_venda: salePrice,
        estoque_inicial: initialStock,
        estoque_minimo: minStock,
        imagem: selectedProduct.imagem,
        galeria: selectedProduct.galeria,
        descricao: selectedProduct.descricao,
        especificacoes: {
          ...selectedProduct.especificacoes,
          'Modo de Comercialização': configMode === 'UN' ? 'Unidade Avulsa' : `Lote de ${batchSize} unidades`,
          'Preço Custo Fornecedor': `R$ ${costPrice.toFixed(2)}`,
        },
        url_origem: selectedProduct.url_origem,
      };

      const res = await apiRequest<any>('/suppliers/import', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setImportSuccessData(res);
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Erro ao importar produto.');
    } finally {
      setImporting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
      <div className="bg-white w-full max-w-5xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header Superior com Logos dos 4 Fornecedores Homologados */}
        <div className="px-6 py-4.5 bg-gradient-to-r from-[#03224C] via-[#053679] to-[#0A4B9E] text-white flex items-center justify-between border-b border-white/10 shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-500 text-white tracking-wide uppercase">
                <Truck className="w-3 h-3" /> Integração Direta de Fornecedores
              </span>
              <span className="text-blue-200 text-xs hidden sm:inline">•</span>
              <span className="text-blue-100 text-xs font-medium hidden sm:inline">
                Sincronização Automática com Bling ERP v3 e Catálogo Local
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-extrabold tracking-tight flex items-center gap-2">
              Importar Catálogo & Produtos Gráficos
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Barra de Fornecedores Parceiros Homologados */}
        <div className="bg-slate-50 px-6 py-2.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
            <span>Parceiros Homologados:</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <a
              href="https://www.atualcard.com.br"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:border-orange-500 font-bold text-slate-700 shadow-2xs hover:text-orange-600 transition-colors"
              title="Atual Card Gráfica"
            >
              <span className="w-2 h-2 rounded-full bg-orange-600"></span>
              Atual Card
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
            <a
              href="https://www.zapgrafica.com.br"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:border-blue-600 font-bold text-slate-700 shadow-2xs hover:text-blue-700 transition-colors"
              title="Zap Gráfica"
            >
              <span className="w-2 h-2 rounded-full bg-blue-600"></span>
              Zap Gráfica
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
            <a
              href="https://www.futuraim.com.br"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:border-emerald-600 font-bold text-slate-700 shadow-2xs hover:text-emerald-700 transition-colors"
              title="FuturaIM"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
              FuturaIM
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
            <a
              href="https://www.padraocolor.com.br"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:border-amber-600 font-bold text-slate-700 shadow-2xs hover:text-amber-700 transition-colors"
              title="Padrão Color"
            >
              <span className="w-2 h-2 rounded-full bg-amber-600"></span>
              Padrão Color
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* Conteúdo Principal do Modal */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {/* Alerta de Erro caso ocorra */}
          {errorMsg && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Atenção na Importação</p>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Se um produto está selecionado para configuração (Drawer de Configuração) */}
          {selectedProduct ? (
            <div className="space-y-6">
              {/* Botão Voltar para o Catálogo */}
              <button
                type="button"
                onClick={() => setSelectedProduct(null)}
                className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1"
              >
                ← Voltar para lista de produtos
              </button>

              {/* Sucesso após Importar */}
              {importSuccessData ? (
                <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-4">
                  <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
                    <CheckCircle className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-emerald-950">
                      Produto Importado e Sincronizado com Sucesso!
                    </h3>
                    <p className="text-xs text-emerald-800 max-w-lg mx-auto mt-1">
                      {importSuccessData.message}
                    </p>
                  </div>

                  <div className="max-w-md mx-auto bg-white p-4 rounded-xl border border-emerald-100 text-left text-xs space-y-2">
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Nome:</span>
                      <span className="font-bold text-slate-800">{importSuccessData.product?.NOME}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Código SKU:</span>
                      <span className="font-mono font-bold text-sky-700">{importSuccessData.product?.CODIGO}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Modo de Venda:</span>
                      <span className="font-semibold text-slate-800">{importSuccessData.product?.UNIDADE}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Preço de Venda:</span>
                      <span className="font-bold text-emerald-600">R$ {Number(importSuccessData.product?.PRECO).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Estoque Inicial Cadastrado:</span>
                      <span className="font-bold text-slate-800">{importSuccessData.product?.ESTOQUE} un/lotes</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Status Bling ERP v3:</span>
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600">
                        <CheckCircle className="w-3.5 h-3.5" /> Sincronizado ({importSuccessData.bling_id || 'ID_EXT OK'})
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct(null);
                        setImportSuccessData(null);
                      }}
                      className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold"
                    >
                      Importar Outro Produto
                    </button>
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20"
                    >
                      Concluir e Ver no Catálogo
                    </button>
                  </div>
                </div>
              ) : (
                /* Formulário de Configuração Comercial */
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Coluna Esquerda: Preview do Produto Extraído */}
                  <div className="lg:col-span-5 space-y-4">
                    <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 space-y-3">
                      <div className="relative rounded-xl overflow-hidden bg-white border border-slate-200 aspect-video flex items-center justify-center">
                        {selectedProduct.imagem ? (
                          <img
                            src={selectedProduct.imagem}
                            alt={selectedProduct.nome}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Box className="w-12 h-12 text-slate-300" />
                        )}
                        <span className="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#03224C] text-white shadow-sm">
                          {selectedProduct.fornecedor_nome}
                        </span>
                      </div>

                      <div>
                        <h3 className="text-sm font-bold text-slate-900 leading-snug">
                          {selectedProduct.nome}
                        </h3>
                        <p className="text-[11px] text-slate-500 mt-1 line-clamp-3">
                          {selectedProduct.descricao}
                        </p>
                      </div>

                      {/* Especificações Técnicas */}
                      {selectedProduct.especificacoes && (
                        <div className="pt-2 border-t border-slate-200">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                            Ficha Técnica do Fornecedor:
                          </span>
                          <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                            {Object.entries(selectedProduct.especificacoes).slice(0, 4).map(([k, v]) => (
                              <div key={k} className="bg-white p-1.5 rounded-md border border-slate-100">
                                <span className="text-slate-400 block text-[9px]">{k}</span>
                                <span className="font-medium text-slate-700 truncate block">{v}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedProduct.url_origem && (
                        <a
                          href={selectedProduct.url_origem}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-sky-600 hover:text-sky-700 font-semibold inline-flex items-center gap-1"
                        >
                          Ver produto no site do fornecedor <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Coluna Direita: Assistente de Configuração Comercial */}
                  <div className="lg:col-span-7 bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-5">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-sky-600" />
                        Configurações de Comercialização & Estoque
                      </h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Defina como esse item será vendido no CRM e registrado no Bling ERP.
                      </p>
                    </div>

                    {/* 1. Modo de Venda (Unidade vs Lote) */}
                    <div>
                      <label className="text-xs font-bold text-slate-700 block mb-2">
                        1. Modo de Venda do Produto
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          type="button"
                          onClick={() => handleModeChange('UN')}
                          className={`p-3 rounded-xl border text-left transition-all ${
                            configMode === 'UN'
                              ? 'border-sky-600 bg-sky-50/60 ring-2 ring-sky-500/20'
                              : 'border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-xs text-slate-900">Por Unidade (UN)</span>
                            <span className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${configMode === 'UN' ? 'border-sky-600 bg-sky-600' : 'border-slate-300'}`}>
                              {configMode === 'UN' && <span className="w-1.5 h-1.5 rounded-full bg-white"></span>}
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500">
                            Venda unitária individual (ex: crachás avulsos, cordões, credenciais).
                          </p>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleModeChange('LOTE')}
                          className={`p-3 rounded-xl border text-left transition-all ${
                            configMode === 'LOTE'
                              ? 'border-sky-600 bg-sky-50/60 ring-2 ring-sky-500/20'
                              : 'border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-xs text-slate-900">Por Lote / Pacote</span>
                            <span className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${configMode === 'LOTE' ? 'border-sky-600 bg-sky-600' : 'border-slate-300'}`}>
                              {configMode === 'LOTE' && <span className="w-1.5 h-1.5 rounded-full bg-white"></span>}
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500">
                            Venda fechada por tiragem (ex: pacote de 50, 100, 500, 1000 un).
                          </p>
                        </button>
                      </div>

                      {/* Seletor de Quantidade do Lote */}
                      {configMode === 'LOTE' && (
                        <div className="mt-3 p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                          <span className="text-[11px] font-bold text-slate-700 block">
                            Selecione a quantidade de peças por lote:
                          </span>
                          <div className="flex flex-wrap items-center gap-1.5">
                            {[25, 50, 100, 250, 500, 1000, 2500].map((qtd) => (
                              <button
                                key={qtd}
                                type="button"
                                onClick={() => handleBatchChange(qtd)}
                                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${
                                  batchSize === qtd
                                    ? 'bg-[#03224C] text-white shadow-xs'
                                    : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                                }`}
                              >
                                {qtd} un
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 2. Formação de Preço e Margem */}
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-slate-700 block">
                        2. Precificação & Formação de Margem Comercial
                      </label>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div>
                          <span className="text-[11px] text-slate-500 block mb-1">
                            Custo do Fornecedor (R$):
                          </span>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs text-slate-400">R$</span>
                            <input
                              type="number"
                              step="0.01"
                              value={costPrice}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setCostPrice(val);
                                setSalePrice(Number((val * (1 + profitMargin / 100)).toFixed(2)));
                              }}
                              className="w-full pl-8 pr-2 py-1.5 rounded-lg border border-slate-200 text-xs font-bold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                            />
                          </div>
                        </div>

                        <div>
                          <span className="text-[11px] text-slate-500 block mb-1">
                            Margem de Lucro (%):
                          </span>
                          <div className="relative">
                            <input
                              type="number"
                              value={profitMargin}
                              onChange={(e) => handleMarginChange(Number(e.target.value))}
                              className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-bold text-sky-700 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                            />
                            <span className="absolute right-2.5 top-2 text-xs text-slate-400">%</span>
                          </div>
                        </div>

                        <div>
                          <span className="text-[11px] font-bold text-emerald-800 block mb-1">
                            Preço de Venda Final (R$):
                          </span>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs text-emerald-600 font-bold">R$</span>
                            <input
                              type="number"
                              step="0.01"
                              value={salePrice}
                              onChange={(e) => handleSalePriceChange(Number(e.target.value))}
                              className="w-full pl-8 pr-2 py-1.5 rounded-lg border border-emerald-300 bg-emerald-50/40 text-xs font-extrabold text-emerald-800 focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Card de Resumo de Rentabilidade */}
                      <div className="p-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-100 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-emerald-600" />
                          <span className="text-emerald-900 font-semibold">
                            Lucro Bruto Estimado:
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="font-extrabold text-emerald-700 text-sm">
                            + R$ {(salePrice - costPrice).toFixed(2)}
                          </span>
                          <span className="text-[10px] text-emerald-600 block">
                            (Markup de {profitMargin}%)
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* 3. Estoque e SKU */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          Quantidade a dar entrada no estoque:
                        </label>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min="0"
                            value={initialStock}
                            onChange={(e) => setInitialStock(Number(e.target.value))}
                            className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-bold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                          />
                          <span className="text-xs text-slate-500 shrink-0">
                            {configMode === 'UN' ? 'unidades' : 'lotes'}
                          </span>
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          Estoque Mínimo para Alerta:
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={minStock}
                          onChange={(e) => setMinStock(Number(e.target.value))}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-bold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                    </div>

                    {/* 4. SKU e Categoria */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          Código SKU / Referência:
                        </label>
                        <input
                          type="text"
                          value={customSku}
                          onChange={(e) => setCustomSku(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-mono font-bold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                        />
                      </div>

                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          Categoria no CRM:
                        </label>
                        <select
                          value={customCategory}
                          onChange={(e) => setCustomCategory(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                        >
                          <option value="Crachás & Identificação">Crachás & Identificação</option>
                          <option value="Cordões & Acessórios">Cordões & Acessórios</option>
                          <option value="Cartões & Papelaria">Cartões & Papelaria</option>
                          <option value="Pastas & Envelopes">Pastas & Envelopes</option>
                          <option value="Comunicação Visual">Comunicação Visual</option>
                        </select>
                      </div>
                    </div>

                    {/* Botão de Ação: Confirmar Importação */}
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={handleConfirmImport}
                        disabled={importing || salePrice <= 0}
                        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-orange-500 via-[#E86014] to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-extrabold text-sm shadow-md shadow-orange-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                      >
                        {importing ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Importando no DBF e Sincronizando com Bling ERP...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            Confirmar Importação (CRM + Bling + Catálogo)
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Modo de Seleção de Produtos (Catálogo ou Link Direto) */
            <div className="space-y-5">
              {/* Abas Superiores */}
              <div className="flex border-b border-slate-200 gap-6">
                <button
                  type="button"
                  onClick={() => setActiveTab('catalog')}
                  className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-colors ${
                    activeTab === 'catalog'
                      ? 'border-sky-600 text-sky-700'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <PackageCheck className="w-4 h-4" />
                  Catálogo Pré-Indexado dos Fornecedores
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('url')}
                  className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-colors ${
                    activeTab === 'url'
                      ? 'border-sky-600 text-sky-700'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <LinkIcon className="w-4 h-4" />
                  Importar por Link / URL do Produto
                </button>
              </div>

              {/* Aba 1: Catálogo dos Fornecedores */}
              {activeTab === 'catalog' && (
                <div className="space-y-4">
                  {/* Barra de Pesquisa e Filtro de Parceiros */}
                  <div className="flex flex-col sm:flex-row gap-3 items-stretch">
                    <form onSubmit={handleSearchSubmit} className="flex-1 relative">
                      <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type="text"
                        placeholder="Buscar por crachá, cordão, cartão de visita, banner, pasta, adesivo..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-9 pr-24 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                      />
                      <button
                        type="submit"
                        className="absolute right-1.5 top-1.5 px-3 py-1.5 rounded-lg bg-sky-600 text-white text-xs font-bold hover:bg-sky-700"
                      >
                        Pesquisar
                      </button>
                    </form>

                    {/* Filtro por Parceiro */}
                    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 shrink-0">
                      <button
                        type="button"
                        onClick={() => handlePartnerFilter('ALL')}
                        className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                          selectedPartnerId === 'ALL'
                            ? 'bg-[#03224C] text-white shadow-xs'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Todos
                      </button>
                      {partners.map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => handlePartnerFilter(p.id)}
                          className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors whitespace-nowrap ${
                            selectedPartnerId === p.id
                              ? 'bg-sky-600 text-white shadow-xs'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          {p.nome}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Grid de Produtos */}
                  {loadingCatalog ? (
                    <div className="py-16 text-center text-slate-400 space-y-2">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto text-sky-600" />
                      <p className="text-xs">Consultando catálogo dos fornecedores...</p>
                    </div>
                  ) : catalogItems.length === 0 ? (
                    <div className="py-16 text-center text-slate-400 space-y-2">
                      <PackageCheck className="w-10 h-10 mx-auto text-slate-300" />
                      <p className="text-xs font-semibold text-slate-600">
                        Nenhum produto encontrado para os termos pesquisados.
                      </p>
                      <p className="text-[11px] text-slate-400">
                        Tente buscar por termos genéricos como "cracha", "cordao", "cartao" ou use a aba de Link / URL.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {catalogItems.map((prod) => (
                        <div
                          key={prod.id}
                          className="bg-white rounded-2xl border border-slate-200 shadow-2xs hover:shadow-md transition-shadow overflow-hidden flex flex-col justify-between group"
                        >
                          <div>
                            <div className="relative aspect-4/3 bg-slate-100 overflow-hidden">
                              <img
                                src={prod.imagem}
                                alt={prod.nome}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                              />
                              <span className="absolute top-2 left-2 px-2 py-0.5 rounded-md text-[9px] font-bold bg-[#03224C]/90 text-white backdrop-blur-xs">
                                {prod.fornecedor_nome}
                              </span>
                              <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md text-[9px] font-bold bg-white/90 text-slate-700 shadow-xs">
                                {prod.categoria}
                              </span>
                            </div>

                            <div className="p-3.5 space-y-2">
                              <h4 className="text-xs font-bold text-slate-900 line-clamp-2 leading-snug">
                                {prod.nome}
                              </h4>
                              <p className="text-[11px] text-slate-500 line-clamp-2">
                                {prod.descricao}
                              </p>

                              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100">
                                <div>
                                  <span className="text-slate-400 block text-[9px]">Custo Base:</span>
                                  <span className="font-bold text-slate-700">
                                    R$ {prod.preco_custo_unit.toFixed(2)} /un
                                  </span>
                                </div>
                                <div className="text-right">
                                  <span className="text-emerald-600 block text-[9px]">Venda Sugerida:</span>
                                  <span className="font-extrabold text-emerald-700">
                                    R$ {prod.preco_venda_sugerido_unit.toFixed(2)} /un
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="p-3.5 pt-0">
                            <button
                              type="button"
                              onClick={() => openConfigDrawer(prod)}
                              className="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-[#03224C] to-[#0A4B9E] hover:from-[#053679] hover:to-[#0C58B6] text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition-colors"
                            >
                              <Sparkles className="w-3.5 h-3.5 text-orange-400" />
                              Configurar Venda & Importar
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Aba 2: Importar por Link / URL */}
              {activeTab === 'url' && (
                <div className="max-w-2xl mx-auto py-4 space-y-6">
                  <div className="text-center space-y-1.5">
                    <div className="w-12 h-12 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center mx-auto">
                      <LinkIcon className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900">
                      Importe Qualquer Produto Colando o Link
                    </h3>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      Cole a URL direta da página do produto na Atual Card, Zap Gráfica, FuturaIM ou Padrão Color. Nós extraímos fotos, especificações e custos automaticamente.
                    </p>
                  </div>

                  <form onSubmit={handleExtractUrl} className="space-y-3">
                    <div className="relative">
                      <LinkIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                      <input
                        type="url"
                        required
                        placeholder="https://www.atualcard.com.br/produto/cracha-pvc..."
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-300 text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-sky-500 shadow-2xs font-mono"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={extractingUrl || !urlInput.trim()}
                      className="w-full py-3 rounded-xl bg-gradient-to-r from-orange-500 to-[#E86014] hover:from-orange-600 hover:to-orange-700 text-white font-bold text-xs shadow-md shadow-orange-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                    >
                      {extractingUrl ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Acessando fornecedor e extraindo fotos e especificações...
                        </>
                      ) : (
                        <>
                          <Search className="w-4 h-4" />
                          Analisar e Extrair Produto do Fornecedor
                        </>
                      )}
                    </button>
                  </form>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                    <span className="font-bold text-slate-700 block">Exemplos de Links Suportados:</span>
                    <ul className="space-y-1 text-slate-500 text-[11px]">
                      <li className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                        <code className="text-slate-700">https://www.atualcard.com.br/produto/cracha-pvc-076mm</code>
                      </li>
                      <li className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                        <code className="text-slate-700">https://www.zapgrafica.com.br/produto/cordao-personalizado</code>
                      </li>
                      <li className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <code className="text-slate-700">https://www.futuraim.com.br/produto/roller-clip-cracha</code>
                      </li>
                      <li className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                        <code className="text-slate-700">https://www.padraocolor.com.br/produto/envelope-oficio</code>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Rodapé do Modal */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 shrink-0">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Importação Segura com Registro Local em DBF e Sync Bling v3</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold text-slate-700"
          >
            Fechar
          </button>
        </div>

      </div>
    </div>
  );
};

