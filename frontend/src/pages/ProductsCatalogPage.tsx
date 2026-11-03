import React, { useEffect, useState } from 'react';
import {
  Eye,
  FolderPlus,
  Grid,
  List,
  Package,
  Plus,
  Search,
  Sparkles,
  Tag,
  X,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import { CategoryRecord, PaginatedResponse, ProductRecord } from '../types/crm';

export const ProductsCatalogPage: React.FC = () => {
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [viewMode, setViewMode] = useState<'cards' | 'list'>('cards');
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<ProductRecord | null>(null);
  const [modalProductOpen, setModalProductOpen] = useState(false);
  const [modalCategoryOpen, setModalCategoryOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [catName, setCatName] = useState('');
  const [catCode, setCatCode] = useState('');

  const [prodForm, setProdForm] = useState({
    CODIGO: '',
    NOME: '',
    DESC_CURTA: '',
    DESCRICAO_COMPLETA: '',
    ID_CATEG: '',
    UNIDADE: 'UN',
    PRECO: 0,
    PRECO_CUST: 0,
    DESC_MAX: 12,
    ESTOQUE: 100,
    DESTAQUE: true,
    SITUACAO: 'ATIVO',
  });

  const loadCatalog = async () => {
    try {
      const params = new URLSearchParams({ page_size: '100' });
      if (search) params.set('search', search);
      if (selectedCategory) params.set('category_id', selectedCategory);
      const [pRes, cRes] = await Promise.all([
        apiRequest<PaginatedResponse<ProductRecord>>(`/products?${params.toString()}`),
        apiRequest<CategoryRecord[]>('/products/categories'),
      ]);
      setProducts(pRes.items);
      setCategories(cRes);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadCatalog();
  }, [search, selectedCategory]);

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/products/categories', {
        method: 'POST',
        body: JSON.stringify({ CODIGO: catCode || undefined, NOME: catName, ORDEM: categories.length + 1 }),
      });
      setCatName('');
      setCatCode('');
      setModalCategoryOpen(false);
      await loadCatalog();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/products', {
        method: 'POST',
        body: JSON.stringify(prodForm),
      });
      setModalProductOpen(false);
      setProdForm({
        CODIGO: '',
        NOME: '',
        DESC_CURTA: '',
        DESCRICAO_COMPLETA: '',
        ID_CATEG: '',
        UNIDADE: 'UN',
        PRECO: 0,
        PRECO_CUST: 0,
        DESC_MAX: 12,
        ESTOQUE: 100,
        DESTAQUE: true,
        SITUACAO: 'ATIVO',
      });
      await loadCatalog();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner Comercial Estilo Loja B2B / Globalcards */}
      <div className="rounded-2xl bg-gradient-to-r from-[#0F3D6E] via-[#0B2D52] to-[#0284C7] text-white p-6 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="bg-white p-2 rounded-xl shadow-md hidden sm:flex items-center justify-center shrink-0">
            <img
              src="/logo-globalcards.jpg"
              alt="Global Cards"
              className="h-9 w-auto object-contain"
            />
          </div>
          <div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/15 text-sky-200 text-[11px] font-semibold mb-1">
              <Sparkles className="w-3.5 h-3.5" /> Catálogo Comercial B2B & Integração Bling
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Catálogo de Produtos e Suprimentos</h1>
            <p className="text-xs text-sky-100/90 mt-0.5 max-w-2xl">
              Organização visual por categorias, consulta rápida de preços, saldos de estoque e ficha técnica comercial para montagem de orçamentos e pedidos.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={() => setModalCategoryOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-semibold border border-white/20"
          >
            <FolderPlus className="w-4 h-4" /> + Categoria
          </button>
          <button
            type="button"
            onClick={() => setModalProductOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold shadow"
          >
            <Plus className="w-4 h-4" /> Novo Produto
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Barra de Categorias + Pesquisa + Alternador Cards/Lista */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Menu Lateral de Categorias (Inspirado na Globalcards) */}
        <div className="w-full lg:w-64 shrink-0 bg-white rounded-xl border border-slate-200 p-4 shadow-sm h-fit">
          <h3 className="text-xs font-bold uppercase text-slate-500 mb-3 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-sky-600" /> Categorias
          </h3>
          <div className="space-y-1">
            <button
              type="button"
              onClick={() => setSelectedCategory('')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold transition ${
                selectedCategory === ''
                  ? 'bg-[#0F3D6E] text-white'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              Todas as Categorias ({products.length})
            </button>
            {categories.map((cat) => (
              <button
                key={cat.ID}
                type="button"
                onClick={() => setSelectedCategory(cat.ID)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition ${
                  selectedCategory === cat.ID
                    ? 'bg-[#0F3D6E] text-white font-semibold'
                    : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                {cat.NOME}
              </button>
            ))}
          </div>
        </div>

        {/* Grade Principal de Produtos */}
        <div className="flex-1 space-y-4">
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Pesquisar produto por nome, código SKU ou especificação..."
                className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-sky-600"
              />
            </div>
            <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden">
              <button
                type="button"
                onClick={() => setViewMode('cards')}
                className={`p-2 ${
                  viewMode === 'cards' ? 'bg-[#0F3D6E] text-white' : 'bg-white text-slate-600'
                }`}
                title="Visualização em Cards"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setViewMode('list')}
                className={`p-2 ${
                  viewMode === 'list' ? 'bg-[#0F3D6E] text-white' : 'bg-white text-slate-600'
                }`}
                title="Visualização em Lista"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>

          {viewMode === 'cards' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {products.map((p) => (
                <div
                  key={p.ID}
                  className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between overflow-hidden group"
                >
                  <div>
                    <div className="h-36 bg-gradient-to-br from-slate-100 to-sky-50 flex items-center justify-center relative border-b border-slate-100">
                      <Package className="w-12 h-12 text-sky-700/40 group-hover:scale-110 transition" />
                      <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-white/90 text-[10px] font-mono font-bold text-slate-700 shadow-2xs">
                        {p.CODIGO}
                      </span>
                      <span
                        className={`absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          p.ORIGEM === 'BLING'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-sky-100 text-sky-800'
                        }`}
                      >
                        {p.ORIGEM}
                      </span>
                    </div>
                    <div className="p-4">
                      <span className="text-[11px] font-semibold text-sky-700 uppercase">
                        {p.CATEGORIA_NOME || 'Catálogo Geral'}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 mt-0.5 line-clamp-2">
                        {p.NOME}
                      </h3>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {p.DESC_CURTA || 'Produto disponível para cotação e pedido imediato.'}
                      </p>
                    </div>
                  </div>

                  <div className="px-4 pb-4 pt-2 border-t border-slate-100 flex items-end justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Preço Unitário ({p.UNIDADE})</span>
                      <span className="text-lg font-extrabold text-[#0F3D6E] tabular-nums">
                        R$ {p.PRECO.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                      <span className="block text-[11px] text-slate-500">
                        Estoque: <strong>{p.ESTOQUE}</strong> {p.UNIDADE}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedProduct(p)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 border border-sky-200/80 text-sky-700 hover:bg-[#0F3D6E] hover:text-white hover:border-[#0F3D6E] text-xs font-semibold transition-colors shadow-2xs"
                    >
                      <Eye className="w-3.5 h-3.5" /> Detalhes
                    </button>
                  </div>
                </div>
              ))}
              {products.length === 0 && (
                <div className="col-span-full bg-white rounded-xl border border-slate-200 p-10 text-center text-xs text-slate-400">
                  Nenhum produto cadastrado nesta categoria.
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto shadow-sm">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px] font-semibold">
                    <th className="py-3 px-4">Código</th>
                    <th className="py-3 px-4">Produto</th>
                    <th className="py-3 px-4">Categoria</th>
                    <th className="py-3 px-4">Preço</th>
                    <th className="py-3 px-4">Estoque</th>
                    <th className="py-3 px-4">Origem</th>
                    <th className="py-3 px-4 text-right">Ficha</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {products.map((p) => (
                    <tr key={p.ID} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-sky-800">{p.CODIGO}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">{p.NOME}</td>
                      <td className="py-3 px-4">{p.CATEGORIA_NOME}</td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-700">
                        R$ {p.PRECO.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 font-mono">
                        {p.ESTOQUE} {p.UNIDADE}
                      </td>
                      <td className="py-3 px-4">{p.ORIGEM}</td>
                      <td className="py-3 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedProduct(p)}
                          className="p-1.5 rounded-lg bg-sky-50 border border-sky-200/80 text-sky-700 hover:bg-sky-100 transition-colors shadow-2xs"
                          title="Visualizar Ficha Técnica"
                        >
                          <Eye className="w-4 h-4 inline" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Detalhamento Individual do Produto */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl p-6 space-y-4">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono text-sky-700 font-bold">
                  SKU: {selectedProduct.CODIGO} • Origem: {selectedProduct.ORIGEM}
                </span>
                <h2 className="text-lg font-bold text-slate-900 mt-0.5">{selectedProduct.NOME}</h2>
              </div>
              <button type="button" onClick={() => setSelectedProduct(null)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-50">
                <span className="text-slate-400 block">Preço Comercial</span>
                <strong className="text-base text-[#0F3D6E]">
                  R$ {selectedProduct.PRECO.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <span className="text-slate-400 block">Estoque Disponível</span>
                <strong className="text-base text-slate-800">
                  {selectedProduct.ESTOQUE} {selectedProduct.UNIDADE}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <span className="text-slate-400 block">Alçada Máx. Desconto</span>
                <strong className="text-base text-emerald-700">{selectedProduct.DESC_MAX}%</strong>
              </div>
            </div>
            <div className="text-xs space-y-2">
              <h4 className="font-bold text-slate-700">Descrição e Informações Comerciais</h4>
              <p className="text-slate-600">
                {selectedProduct.DETAILS?.full_description ||
                  selectedProduct.DESC_CURTA ||
                  'Sem descrição detalhada adicional.'}
              </p>
              <p className="text-[11px] text-slate-400 font-mono">
                ID Bling: {selectedProduct.ID_EXT || 'Registro Local CRM'} • Última atualização:{' '}
                {selectedProduct.DT_ATUA}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nova Categoria */}
      {modalCategoryOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateCategory}
            className="bg-white rounded-2xl p-6 w-full max-w-md space-y-4 text-xs"
          >
            <h3 className="text-base font-bold text-slate-900">Nova Categoria de Produtos</h3>
            <div>
              <label className="font-semibold block mb-1">Código (opcional)</label>
              <input
                type="text"
                value={catCode}
                onChange={(e) => setCatCode(e.target.value)}
                placeholder="Ex: CRACHAS_PVC"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Nome da Categoria *</label>
              <input
                type="text"
                required
                value={catName}
                onChange={(e) => setCatName(e.target.value)}
                placeholder="Ex: Crachás e Identificação RFID"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setModalCategoryOpen(false)}
                className="px-4 py-2 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-[#0F3D6E] text-white font-semibold"
              >
                Criar Categoria
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Novo Produto */}
      {modalProductOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateProduct}
            className="bg-white rounded-2xl p-6 w-full max-w-xl space-y-3 text-xs"
          >
            <h3 className="text-base font-bold text-slate-900">Cadastrar Produto no Catálogo</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Código SKU</label>
                <input
                  type="text"
                  value={prodForm.CODIGO}
                  onChange={(e) => setProdForm({ ...prodForm, CODIGO: e.target.value })}
                  placeholder="Automático se vazio"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Categoria</label>
                <select
                  value={prodForm.ID_CATEG}
                  onChange={(e) => setProdForm({ ...prodForm, ID_CATEG: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">Geral</option>
                  {categories.map((c) => (
                    <option key={c.ID} value={c.ID}>
                      {c.NOME}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="font-semibold block mb-1">Nome Comercial do Produto *</label>
              <input
                type="text"
                required
                value={prodForm.NOME}
                onChange={(e) => setProdForm({ ...prodForm, NOME: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Descrição Resumida</label>
              <input
                type="text"
                value={prodForm.DESC_CURTA}
                onChange={(e) => setProdForm({ ...prodForm, DESC_CURTA: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="font-semibold block mb-1">Preço Venda (R$) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={prodForm.PRECO}
                  onChange={(e) => setProdForm({ ...prodForm, PRECO: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Estoque Inicial</label>
                <input
                  type="number"
                  step="1"
                  value={prodForm.ESTOQUE}
                  onChange={(e) => setProdForm({ ...prodForm, ESTOQUE: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Desconto Máx (%)</label>
                <input
                  type="number"
                  step="0.5"
                  value={prodForm.DESC_MAX}
                  onChange={(e) => setProdForm({ ...prodForm, DESC_MAX: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setModalProductOpen(false)}
                className="px-4 py-2 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-lg bg-[#0F3D6E] text-white font-semibold"
              >
                Salvar Produto
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

