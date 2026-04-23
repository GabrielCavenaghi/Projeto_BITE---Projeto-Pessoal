import customtkinter as ctk
import json
import os
import datetime
import random
import re

# Importa funções auxiliares do módulo principal (ou de utils)
from ficha import (
    normalizar_ficha, salvar_ficha, calcular_pontos_disponiveis_ficha,
    avaliar_formula, construir_contexto_base, LIMITE_NORMAL, LIMITE_ABSOLUTO
)

from utils.Efeitos_Scalling import ALVOS_DISPONIVEIS, avaliar_efeitos

# Importa todos os painéis e componentes necessários

from .Barra_Recurso import BarraRecurso
from .Painel_Anotacoes import PainelAnotacoes
from .Painel_EditorSkilltree import EditorSkilltree
from .Painel_EstiloLuta import PainelEstiloLuta
from .Painel_Feiticos import PainelFeiticos
from .Painel_Inventario import PainelInventario
from .Painel_Pericias import PainelPericias
from .Painel_Resumo import PainelResumo
from .Painel_Skilltree import PainelSkilltree
from .Painel_Tecnica import PainelTecnica
from .Painel_Habilidades import PainelHabilidades
from .Painel_Combate import PainelCombate

class FichaPersonagem:
    """
    Tela de gerenciamento de ficha — substitui a janela do gerenciador.

    Parâmetros
    ----------
    app       : janela ctk.CTk existente (reutilizada)
    ficha     : dict normalizado com _arquivo preenchido
    on_voltar : callback chamado ao clicar Voltar
    """

    ABA_NOMES = [
        "Combate",
        "Perícias",
        "Skill Tree",
        "Feitiços",
        "Habilidades",
        "Estilo de Luta",
        "Técnica",
        "Inventário",
        "Resumo",
        "Anotações",
    ]

    CORES_RECURSO = {
        "pv":  "#e74c3c",
        "san": "#3498db",
        "pe":  "#f39c12",
    }

    CORES_ATRIBUTO = {
        "AGI": "#e67e22", "FOR": "#e74c3c",
        "INT": "#3498db", "VIG": "#2ecc71",
        "PRE": "#9b59b6",
    }

    def __init__(self, app: ctk.CTk, ficha: dict, on_voltar=None):
        self.app       = app
        self.ficha     = normalizar_ficha(ficha)
        self.on_voltar = on_voltar

        self._aba_ativa   = 0
        self._paineis_aba: dict[int, ctk.CTkFrame] = {}
        self._barras:      dict[str, BarraRecurso]  = {}

        # ══════════════════════════════════════════════════════════════════════
        # NOVO: Controle de atributos editáveis
        # ══════════════════════════════════════════════════════════════════════
        self._attr_widgets = {}        # guarda referências aos labels de valor
        self._lbl_pontos_disponiveis = None  # será criado depois
        # ══════════════════════════════════════════════════════════════════════

        self._fontes()
        self._construir()

    # ── Fontes ────────────────────────────────────────────────────────────────

    def _fontes(self):
        self.f_titulo    = ctk.CTkFont(size=22, weight="bold")
        self.f_subtitulo = ctk.CTkFont(size=13)
        self.f_secao     = ctk.CTkFont(size=12, weight="bold")
        self.f_valor     = ctk.CTkFont(size=20, weight="bold")
        self.f_label     = ctk.CTkFont(size=11)
        self.f_botao     = ctk.CTkFont(size=13)

    # ── Layout geral ──────────────────────────────────────────────────────────

    def _construir(self):
        for w in self.app.winfo_children():
            w.destroy()

        self.app.geometry("1100x700")
        self.app.minsize(900, 560)
        self.app.title(f"Projeto BITE — {self.ficha.get('nome', 'Ficha')}")

        raiz = ctk.CTkFrame(self.app, fg_color="transparent")
        raiz.pack(fill="both", expand=True, padx=16, pady=16)
        raiz.columnconfigure(1, weight=1)
        raiz.rowconfigure(0, weight=1)

        # Painel lateral fixo
        self._lateral = ctk.CTkFrame(raiz, width=280, corner_radius=12,
                                     fg_color="#161616", border_width=1,
                                     border_color="#2a2a2a")
        self._lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._lateral.grid_propagate(False)

        # Área principal
        self._area = ctk.CTkFrame(raiz, corner_radius=12,
                                  fg_color="#161616", border_width=1,
                                  border_color="#2a2a2a")
        self._area.grid(row=0, column=1, sticky="nsew")
        self._area.rowconfigure(1, weight=1)
        self._area.columnconfigure(0, weight=1)

        self._construir_lateral()
        self._construir_abas()
        self._mostrar_aba(0)
        # Atalho de teclado para debug (Ctrl+D)
        self.app.bind("<Control-d>", self._debug_popup)
                
        self._recalcular_tudo()

    # ── Painel lateral ────────────────────────────────────────────────────────

    def _construir_lateral(self):
        lat = self._lateral

        # Botão voltar
        ctk.CTkButton(lat, text="← Voltar", font=self.f_botao, width=90,
                      fg_color="transparent", border_width=1,
                      border_color="#333333",
                      command=self._voltar).pack(anchor="nw", padx=12, pady=(12, 0))

        # Identidade
        ctk.CTkLabel(lat, text=self.ficha.get("nome", "—"),
                     font=self.f_titulo,
                     wraplength=240).pack(pady=(10, 2), padx=16)

        ctk.CTkLabel(lat,
                     text=f"{self.ficha.get('classe','—')}  ·  {self.ficha.get('trilha','—')}",
                     font=self.f_subtitulo, text_color="#888888",
                     wraplength=240).pack(pady=(0, 2), padx=16)

                # Frame para NEX e Grau editáveis
        frame_nex_grau = ctk.CTkFrame(lat, fg_color="transparent")
        frame_nex_grau.pack(fill="x", padx=16, pady=(0, 10))

        # NEX
        ctk.CTkLabel(frame_nex_grau, text="NEX:", font=ctk.CTkFont(size=11),
                     text_color="#888888").pack(side="left")

        opcoes_nex = self._listar_opcoes_nex()
        # Ordena para exibição mais lógica (opcional)
        opcoes_nex.sort(key=lambda x: float(x.replace('%', '')) if x != "99.99%" else 99.99)

        self._nex_var = ctk.StringVar(value=self.ficha.get("nex", "5%"))
        nex_menu = ctk.CTkOptionMenu(
            frame_nex_grau,
            values=opcoes_nex,
            variable=self._nex_var,
            width=75,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._ao_mudar_nex
        )
        nex_menu.pack(side="left", padx=(4, 12))

        # Grau
        ctk.CTkLabel(frame_nex_grau, text="Grau:", font=ctk.CTkFont(size=11),
                     text_color="#888888").pack(side="left")

        opcoes_grau = self._listar_opcoes_grau()
        self._grau_var = ctk.StringVar(value=self.ficha.get("grau", "Grau 4"))
        grau_menu = ctk.CTkOptionMenu(
            frame_nex_grau,
            values=opcoes_grau,
            variable=self._grau_var,
            width=120,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._ao_mudar_grau
        )
        grau_menu.pack(side="left", padx=(4, 0))

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

        rec_frame = ctk.CTkFrame(lat, fg_color="transparent")
        rec_frame.pack(fill="x", padx=16, pady=12)

        estado = self.ficha["estado"]
        specs = [
            ("PV",       "pv",  "pv_atual",  "pv_maximo"),
            ("Sanidade", "san", "san_atual",  "san_maximo"),
            ("PE",       "pe",  "pe_atual",   "pe_maximo"),
        ]

        for nome_exib, chave, k_atual, k_max in specs:
            barra = BarraRecurso(
                rec_frame,   # <--- aqui muda de rec_scroll para rec_frame
                label    = nome_exib,
                atual    = estado.get(k_atual, 0),
                maximo   = estado.get(k_max,   0),
                cor_barra= self.CORES_RECURSO[chave],
                on_change= self._make_callback(chave, k_atual, k_max),
            )
            barra.pack(fill="x", pady=(0, 14))
            self._barras[chave] = barra

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

        # ══════════════════════════════════════════════════════════════════════
        # Atributos (EDITÁVEIS)
        # ══════════════════════════════════════════════════════════════════════
        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12, pady=(6, 6))

        # Cabeçalho com pontos disponíveis
        header_attr = ctk.CTkFrame(lat, fg_color="transparent")
        header_attr.pack(fill="x", padx=16, pady=(4, 6))

        ctk.CTkLabel(header_attr, text="ATRIBUTOS",
                     font=self.f_secao, text_color="#555555").pack(side="left")

        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)
        self._lbl_pontos_disponiveis = ctk.CTkLabel(
            header_attr,
            text=f"{pontos_disp} pts",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1c40f" if pontos_disp > 0 else "#888888"
        )
        self._lbl_pontos_disponiveis.pack(side="right")

        # Scroll frame para os atributos (caso haja muitos)
        attr_scroll = ctk.CTkScrollableFrame(lat, fg_color="transparent", height=200)
        attr_scroll.pack(fill="x", padx=8, pady=(0, 8))

        # Container interno (para alinhamento)
        attr_container = ctk.CTkFrame(attr_scroll, fg_color="transparent")
        attr_container.pack(fill="x")

        # Para cada atributo, criar uma linha com: sigla | valor | [+] [-]
        for sigla, valor in self.ficha.get("atributos", {}).items():
            cor = self.CORES_ATRIBUTO.get(sigla, "#888888")

            linha = ctk.CTkFrame(attr_container, fg_color="transparent")
            linha.pack(fill="x", pady=2)

            # Sigla do atributo
            ctk.CTkLabel(linha, text=sigla,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=cor, width=40).pack(side="left", padx=(8, 4))

            # Valor atual
            lbl_valor = ctk.CTkLabel(linha, text=str(valor),
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#ffffff", width=30)
            lbl_valor.pack(side="left", padx=4)
            self._attr_widgets[sigla] = lbl_valor

            # Botão diminuir (-)
            btn_menos = ctk.CTkButton(
                linha, text="−", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, -1)
            )
            btn_menos.pack(side="right", padx=2)

            # Botão aumentar (+)
            btn_mais = ctk.CTkButton(
                linha, text="+", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, +1)
            )
            btn_mais.pack(side="right", padx=2)

        # ══════════════════════════════════════════════════════════════════════
        # Pontos extras (buffs temporários)
        # ══════════════════════════════════════════════════════════════════════
        extras_frame = ctk.CTkFrame(lat, fg_color="transparent")
        extras_frame.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(extras_frame, text="Pontos extras:",
                     font=ctk.CTkFont(size=11), text_color="#666666").pack(side="left")

        self._entrada_extras = ctk.CTkEntry(extras_frame, width=50, height=26,
                                            font=ctk.CTkFont(size=12),
                                            placeholder_text="0")
        self._entrada_extras.pack(side="left", padx=(4, 4))

        ctk.CTkButton(extras_frame, text="Adicionar", width=70, height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._adicionar_pontos_extras).pack(side="left")

        # Indicador de salvamento
        self._lbl_salvo = ctk.CTkLabel(lat, text="",
                                       font=ctk.CTkFont(size=10),
                                       text_color="#444444")
        self._lbl_salvo.pack(pady=(8, 4), padx=16)

        # ══════════════════════════════════════════════════════════════════════
        # Botão Recalcular (PV / PE / SAN)
        # ══════════════════════════════════════════════════════════════════════
        btn_recalcular = ctk.CTkButton(
            lat,
            text="⟲ Recalcular PV/PE/SAN",
            font=ctk.CTkFont(size=11),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            border_width=1,
            border_color="#444444",
            command=self._recalcular_tudo
        )
        btn_recalcular.pack(fill="x", padx=16, pady=(4, 4))

    def _make_callback(self, chave: str, k_atual: str, k_max: str):
        """Fábrica de callbacks para as barras de recurso."""
        def callback(_valor_ignorado: int):
            barra = self._barras[chave]
            self.ficha["estado"][k_atual] = barra.get_atual()
            self.ficha["estado"][k_max]   = barra.get_maximo()
            self._salvar()
        return callback

    # ── Abas ──────────────────────────────────────────────────────────────────

    def _construir_abas(self):
        area = self._area

        nav = ctk.CTkScrollableFrame(area, fg_color="#0f0f0f", height=48,
                              orientation="horizontal", corner_radius=0)
        nav.grid(row=0, column=0, sticky="ew")

        self._botoes_aba: list[ctk.CTkButton] = []
        for i, nome in enumerate(self.ABA_NOMES):
            btn = ctk.CTkButton(
                nav, text=nome, height=42, font=self.f_botao,
                fg_color="transparent", text_color="#666666",
                hover_color="#1a1a1a", corner_radius=0,
                command=lambda idx=i: self._mostrar_aba(idx),
            )
            btn.pack(side="left", padx=2)
            self._botoes_aba.append(btn)

        self._frame_conteudo = ctk.CTkFrame(area, fg_color="transparent")
        self._frame_conteudo.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        self._frame_conteudo.rowconfigure(0, weight=1)
        self._frame_conteudo.columnconfigure(0, weight=1)

    def _mostrar_aba(self, idx: int):
        self._aba_ativa = idx

        for i, btn in enumerate(self._botoes_aba):
            if i == idx:
                btn.configure(text_color="#ffffff", fg_color="#1e1e1e")
            else:
                btn.configure(text_color="#666666", fg_color="transparent")

        for painel in self._paineis_aba.values():
            painel.grid_forget()

        if idx not in self._paineis_aba:
            self._paineis_aba[idx] = self._criar_painel(idx)

        self._paineis_aba[idx].grid(row=0, column=0, sticky="nsew")

    def _criar_painel(self, idx: int) -> ctk.CTkFrame:
        """Instancia o painel correto para cada índice de aba."""
        nome = self.ABA_NOMES[idx]
        pai  = self._frame_conteudo

        fabricas = {
            "Combate":         lambda: PainelCombate(pai, self.ficha, on_save=self._salvar),
            "Perícias":        lambda: PainelPericias(pai, self.ficha),
            "Skill Tree":      lambda: PainelSkilltree(pai, self.ficha, on_change=self._recalcular_tudo),
            "Feitiços":        lambda: PainelFeiticos(pai, self.ficha, on_passiva_change=self._recalcular_tudo, on_save=self._salvar),
            "Estilo de Luta":  lambda: PainelEstiloLuta(pai, self.ficha, on_save=self._salvar),
            "Técnica":         lambda: PainelTecnica(pai, self.ficha, on_save=self._salvar),
            "Habilidades":     lambda: PainelHabilidades(pai, self.ficha, on_change=self._recalcular_tudo, on_save=self._salvar),
            "Inventário":      lambda: PainelInventario(pai, self.ficha, on_save=self._salvar),
            "Resumo":          lambda: PainelResumo(pai, self.ficha, info_grau=self._carregar_graus().get(self.ficha.get("grau", "Grau 4"), {}), atributos=self.ficha.get("atributos", {})),
            "Anotações":       lambda: PainelAnotacoes(pai, self.ficha, on_save=self._salvar),
        }

        fabrica = fabricas.get(nome)
        if fabrica:
            return fabrica()

        # Fallback genérico para abas ainda não implementadas
        frame = ctk.CTkFrame(pai, fg_color="transparent")
        ctk.CTkLabel(frame, text=f"'{nome}' em construção.",
                     text_color="gray").pack(pady=40)
        return frame

    def _abrir_editor_skilltree(self):
        # Importa a classe EditorSkilltree (definida abaixo)
        editor = EditorSkilltree(self.app, self.ficha, on_close=self._recalcular_tudo)
        editor.abrir()

    # ── Persistência ──────────────────────────────────────────────────────────

    def _salvar(self):
        salvar_ficha(self.ficha)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._lbl_salvo.configure(text=f"salvo às {ts}")

    # ── Navegação ─────────────────────────────────────────────────────────────

    # ══════════════════════════════════════════════════════════════════════════
    # Manipulação de atributos (edição na lateral)
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_ui_atributos(self):
        """Atualiza labels de valor e pontos disponíveis após alteração."""
        # Atualiza labels de valor
        for sigla, lbl in self._attr_widgets.items():
            valor = self.ficha["atributos"][sigla]
            lbl.configure(text=str(valor))

        # Recalcula e atualiza pontos disponíveis
        pontos = calcular_pontos_disponiveis_ficha(self.ficha)
        if self._lbl_pontos_disponiveis:
            self._lbl_pontos_disponiveis.configure(
                text=f"{pontos} pts",
                text_color="#f1c40f" if pontos > 0 else "#888888"
            )

        # Salva automaticamente
        self._salvar()

    def _ajustar_atributo(self, sigla: str, delta: int):
        """Aumenta ou diminui o valor do atributo, respeitando limites e pontos disponíveis."""
        valor_atual = self.ficha["atributos"][sigla]
        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)

        if delta > 0:
            # Aumentar: precisa de pontos e não pode ultrapassar LIMITE_NORMAL
            if pontos_disp <= 0:
                return  # Poderia tocar um aviso sonoro, mas por ora silencioso
            if valor_atual >= LIMITE_NORMAL:
                return
            self.ficha["atributos"][sigla] += 1
            self.ficha["pontos_atributo_gastos"] = self.ficha.get("pontos_atributo_gastos", 0) + 1
        else:  # delta < 0
            # Diminuir: não pode ficar abaixo de 0
            if valor_atual <= 0:
                return
            self.ficha["atributos"][sigla] -= 1
            self.ficha["pontos_atributo_gastos"] = max(0, self.ficha.get("pontos_atributo_gastos", 0) - 1)

        self._atualizar_ui_atributos()


    def _calcular_bonus_passivas(self) -> dict:
        db_feiticos = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminhos = [
            os.path.join(base_dir, "data", "feiticos.json"),
            os.path.join(base_dir, "data", "feiticos_custom.json")
        ]
        for caminho in caminhos:
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    for item in json.load(f):
                        db_feiticos[item["id"]] = item

        contexto = construir_contexto_base(self.ficha)
        bonificacoes = {}

        # Processa habilidades gerais passivas
        for hab in self.ficha.get("habilidades_gerais", []):
            if hab.get("tipo") != "Passiva":
                continue
            hab_id = hab["id"]
            if hab_id not in self.ficha.get("passivas_ativas", {}):
                continue
            for efeito in hab.get("efeitos", []):
                alvo = efeito["alvo"]
                operacao = efeito["operacao"]
                formula = efeito["formula"]
                valor = avaliar_formula(formula, contexto)

                if alvo not in bonificacoes:
                    bonificacoes[alvo] = 0

                if operacao == "+":
                    bonificacoes[alvo] += valor
                elif operacao == "-":
                    bonificacoes[alvo] -= valor
                elif operacao == "=":
                    bonificacoes[alvo] = valor
        
        for feat_id, versao in self.ficha.get("passivas_ativas", {}).items():
            feitico = db_feiticos.get(feat_id)
            if not feitico or feitico.get("tipo") != "Passiva":
                continue
            efeitos_versao = feitico.get("efeitos_por_versao", {}).get(versao, [])
            if not efeitos_versao and versao != "BASE":
                efeitos_versao = feitico.get("efeitos_por_versao", {}).get("BASE", [])

            for efeito in efeitos_versao:
                alvo = efeito["alvo"]
                operacao = efeito["operacao"]
                formula = efeito["formula"]
                valor = avaliar_formula(formula, contexto)

                if alvo not in bonificacoes:
                    bonificacoes[alvo] = 0

                if operacao == "+":
                    bonificacoes[alvo] += valor
                elif operacao == "-":
                    bonificacoes[alvo] -= valor
                elif operacao == "=":
                    bonificacoes[alvo] = valor

        return bonificacoes

    def recalcular_bonus_skilltree(self) -> dict:
        """Retorna um dicionário com os bônus acumulados da Skill Tree."""
        bonificacoes = {}
        nos_comprados = self.ficha.get("nos_comprados", {})
        if not nos_comprados:
            return bonificacoes

        # Carrega o banco da skill tree
        db_skilltree = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "skilltrees.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                for atributo, conteudo in data.items():
                    for no in conteudo.get("nos", []):
                        db_skilltree[no["id"]] = no

        contexto = construir_contexto_base(self.ficha)

        for atributo, ids in nos_comprados.items():
            for no_id in ids:
                no = db_skilltree.get(no_id)
                if not no:
                    continue
                for efeito in no.get("efeitos", []):
                    alvo = efeito["alvo"]
                    operacao = efeito["operacao"]
                    formula = efeito["formula"]
                    valor = avaliar_formula(formula, contexto)

                    if alvo not in bonificacoes:
                        bonificacoes[alvo] = 0

                    if operacao == "+":
                        bonificacoes[alvo] += valor
                    elif operacao == "-":
                        bonificacoes[alvo] -= valor
                    elif operacao == "=":
                        bonificacoes[alvo] = valor

        return bonificacoes

    def _adicionar_pontos_extras(self):
        """Adiciona pontos temporários (buffs) ao pool disponível."""
        texto = self._entrada_extras.get().strip()
        if not texto:
            return
        try:
            qtd = int(texto)
        except ValueError:
            return
        if qtd <= 0:
            return

        # Armazena como campo separado (não interfere nos gastos fixos)
        self.ficha["pontos_extras_temp"] = self.ficha.get("pontos_extras_temp", 0) + qtd
        self._entrada_extras.delete(0, "end")
        self._atualizar_ui_atributos()

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()


    # ══════════════════════════════════════════════════════════════════════════
    # Progressão de NEX e Grau
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar_progressao_nex(self) -> dict:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "progressao_nex.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _carregar_classes(self) -> dict:
        """Carrega o dicionário de classes (nome -> dados)."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "classes.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                lista = json.load(f)
                resultado = {item["nome"]: item for item in lista}
                return resultado
        print("Arquivo classes.json não encontrado em:", caminho)
        return {}
        

    def _carregar_graus(self) -> dict:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "graus.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("graus", {})
        return {}
    
    def calcular_valor_pericia(ficha: dict, nome_pericia: str) -> int:
        """Retorna o valor total da perícia (atributo efetivo + treinamento + bônus)."""
        pericia = ficha.get("pericias", {}).get(nome_pericia)
        if not pericia:
            return 0

        atributos = ficha.get("atributos", {})
        attr_override = pericia.get("atributo_override")
        attr_base = pericia.get("atributo_base", "FOR")

        atributo_valor = atributos.get(attr_override if attr_override else attr_base, 0)

        treinamento = pericia.get("treinamento", 0)
        bonus = pericia.get("bonus", 0)

        return atributo_valor + treinamento + bonus

    def _listar_opcoes_nex(self) -> list:
        """Retorna lista de NEX disponíveis (ex.: ['5%', '10%', ...])."""
        progressao = self._carregar_progressao_nex()
        return list(progressao.keys())

    def _listar_opcoes_grau(self) -> list:
        graus = self._carregar_graus()
        # Ordem desejada (pode ajustar)
        ordem = ["Grau 4", "Grau 3", "Grau 2", "Grau 1",
                 "Grau Semi Especial", "Grau Especial", "Grau Ultra Especial"]
        return [g for g in ordem if g in graus]

    def _ao_mudar_nex(self, novo_nex: str):
        self.ficha["nex"] = novo_nex
        self.ficha["pontos_atributo_gastos"] = 0
        self.ficha["pontos_extras_temp"] = 0
        self._recalcular_tudo()
        self._atualizar_ui_atributos()
        self._salvar()

    def _ao_mudar_grau(self, novo_grau: str):
        self.ficha["grau"] = novo_grau
        self._recalcular_tudo()
        self._salvar()

    def _recalcular_totais_nex(self):
        progressao = self._carregar_progressao_nex()
        nex_atual = self.ficha.get("nex", "5%")

        campos_possiveis = [
            "pontos_atributo", "feiticos", "graus_treinamento",
            "habilidade_trilha", "afinidade", "expansao_modo",
            "melhorias_superiores", "habilidades_lendarias", "habilidade_tecnica_n6"
        ]
        totais = {campo: 0 for campo in campos_possiveis}

        for nivel, bonus in progressao.items():
            for campo in campos_possiveis:
                totais[campo] += bonus.get(campo, 0)
            if nivel == nex_atual:
                break

        # 🔁 Atualiza o LP natural antes de calcular recursos
        self._atualizar_lp_base()

        self.ficha["totais_nex"] = totais

    def _atualizar_lp_base(self):
        """Define o LP baseado no NEX atual."""
        progressao = self._carregar_progressao_nex()
        nex_atual = self.ficha.get("nex", "5%")
        lp_base = progressao.get(nex_atual, {}).get("lp", 1)
        self.ficha["lp"] = lp_base
           

    def _atualizar_recursos_por_grau_e_nex(self):
        # Carrega dados
        graus = self._carregar_graus()
        classes = self._carregar_classes()
        grau_atual = self.ficha.get("grau", "Grau 4")
        info_grau = graus.get(grau_atual, {})
        classe_nome = self.ficha.get("classe", "")
        info_classe = classes.get(classe_nome, {})

        atributos = self.ficha.get("atributos", {})
        vig = atributos.get("VIG", 1)
        pre = atributos.get("PRE", 1)

        # -----------------------------------------------------------------
        # 1. Atualiza o LP baseado no NEX
        # -----------------------------------------------------------------
        
        lp_base = self.ficha.get("lp", 1)

        # -----------------------------------------------------------------
        # 2. Determina os multiplicadores (agora por LP, não por NEX)
        # -----------------------------------------------------------------
        pv_por_lp = 0
        san_por_lp = 0
        pe_por_lp = 0

        if "classes" in info_grau and classe_nome in info_grau["classes"]:
            bonus_classe = info_grau["classes"][classe_nome]
            pv_por_lp = bonus_classe.get("pv_por_nex", 0)   # mantém nome original do JSON
            san_por_lp = bonus_classe.get("san_por_nex", 0)
            pe_por_lp = bonus_classe.get("pe_por_nex", 0)
        elif "pv_por_nex" in info_grau:
            pv_por_lp = info_grau.get("pv_por_nex", 0)
            san_por_lp = info_grau.get("san_por_nex", 0)
            pe_por_lp = info_grau.get("pe_por_nex", 0)
        else:
            pv_por_lp = info_classe.get("pv_por_nex", 0)
            san_por_lp = info_classe.get("san_por_nex", 0)
            pe_por_lp = info_classe.get("pe_por_nex", 0)

        # -----------------------------------------------------------------
        # 3. Valores iniciais da classe (base)
        # -----------------------------------------------------------------
        pv_inicial = info_classe.get("pv_inicial", 0)
        san_inicial = info_classe.get("san_inicial", 0)
        pe_inicial = info_classe.get("pe_inicial", 0)

        # -----------------------------------------------------------------
        # 4. Bônus por LP (multiplicação)
        # -----------------------------------------------------------------
        pv_por_lp_total = lp_base * pv_por_lp
        san_por_lp_total = lp_base * san_por_lp
        pe_por_lp_total = lp_base * pe_por_lp

        # -----------------------------------------------------------------
        # 5. Bônus especiais do Grau (Vigor e Presença)
        # -----------------------------------------------------------------
        bonus_vigor = info_grau.get("bonus_vigor", {})
        bonus_presenca = info_grau.get("bonus_presenca", {})

        pv_bonus_vigor = bonus_vigor.get("pv_por_vigor", 0) * vig
        pe_bonus_presenca = bonus_presenca.get("pe_por_presenca", 0) * pre

        # -----------------------------------------------------------------
        # 6. PE adicional por feitiços concedidos pelo NEX
        # -----------------------------------------------------------------
        pe_feiticos = self.ficha.get("totais_nex", {}).get("feiticos", 0)

        # -----------------------------------------------------------------
        # 7. Cálculo final
        # -----------------------------------------------------------------
        pv_max = pv_inicial + pv_por_lp_total + pv_bonus_vigor
        san_max = san_inicial + san_por_lp_total
        pe_max = pe_inicial + pe_por_lp_total + pe_bonus_presenca + pe_feiticos

        # -----------------------------------------------------------------
        # Aplica bônus passivos (Skill Tree + Feitiços)
        # -----------------------------------------------------------------
        bonus = self.ficha.get("bonus_passivos", {})
        pv_max += bonus.get("PV_MAX", 0)
        san_max += bonus.get("SAN_MAX", 0)
        pe_max += bonus.get("PE_MAX", 0)

        # Se o Grau não forneceu multiplicadores, mantém LP (fallback)
        if pv_por_lp == 0 and pv_bonus_vigor == 0:
            pv_max = lp_base
        if san_por_lp == 0:
            san_max = lp_base

        # -----------------------------------------------------------------
        # 8. Atualiza estado e barras
        # -----------------------------------------------------------------
        estado = self.ficha.setdefault("estado", {})
        estado["pv_maximo"] = pv_max
        estado["san_maximo"] = san_max
        estado["pe_maximo"] = pe_max

        estado["pv_atual"] = min(estado.get("pv_atual", pv_max), pv_max)
        estado["san_atual"] = min(estado.get("san_atual", san_max), san_max)
        estado["pe_atual"] = min(estado.get("pe_atual", pe_max), pe_max)

        for chave, barra in self._barras.items():
            if chave == "pv":
                barra.set_valores(estado["pv_atual"], pv_max)
            elif chave == "san":
                barra.set_valores(estado["san_atual"], san_max)
            elif chave == "pe":
                barra.set_valores(estado["pe_atual"], pe_max)

    def _calcular_totais_grau(self) -> dict:
        """Retorna um dicionário com os totais acumulados de Grau."""
        graus = self._carregar_graus()
        grau_atual = self.ficha.get("grau", "Grau 4")
        atributos = self.ficha.get("atributos", {})
        ab = atributos.get("INT", 1)

        # Ordem de progressão (do mais fraco ao mais forte)
        ordem = ["Grau 4", "Grau 3", "Grau 2", "Grau 1",
                 "Grau Semi Especial", "Grau Especial", "Grau Ultra Especial"]

        totais = {
            "pontos_atributo": 0,
            "graus_treinamento": 0,
            "encantamentos": 0,
            "maldicoes": 0,
            "encantamentos_ab_acumulado": 0,  # armazena quantas vezes "metade_ab" foi aplicado
        }

        for grau_nome in ordem:
            info = graus.get(grau_nome, {})
            if not info:
                continue

            # Acumula valores simples
            totais["pontos_atributo"] += info.get("pontos_atributo", 0)
            totais["graus_treinamento"] += info.get("graus_treinamento", 0)
            totais["maldicoes"] += info.get("maldicoes", 0)

            # Tratamento de encantamentos
            if "encantamentos_ab" in info:
                # Cada ocorrência de "encantamentos_ab" conta como uma aplicação de AB/2
                totais["encantamentos_ab_acumulado"] += 1
            else:
                # Acumula encantamentos fixos
                totais["encantamentos"] += info.get("encantamentos", 0)

            if grau_nome == grau_atual:
                break

        # Calcula o valor total de encantamentos
        encantamentos_total = totais["encantamentos"]
        if totais["encantamentos_ab_acumulado"] > 0:
            encantamentos_total += totais["encantamentos_ab_acumulado"] * (ab / 2)

        # Prepara o dicionário final para exibição
        resultado = {
            "pontos_atributo": totais["pontos_atributo"],
            "graus_treinamento": totais["graus_treinamento"],
            "encantamentos": encantamentos_total,
            "maldicoes": totais["maldicoes"],
        }

        # Adiciona bônus especiais do grau atual (não acumulativos)
        info_atual = graus.get(grau_atual, {})
        bonus_vigor = info_atual.get("bonus_vigor", {})
        bonus_presenca = info_atual.get("bonus_presenca", {})

        if bonus_vigor:
            resultado["bonus_vigor"] = {
                "nome": bonus_vigor.get("nome", "Bônus de Vigor"),
                "valor": bonus_vigor.get("pv_por_vigor", 0) * atributos.get("VIG", 1)
            }
        if bonus_presenca:
            resultado["bonus_presenca"] = {
                "nome": bonus_presenca.get("nome", "Bônus de Presença"),
                "valor": bonus_presenca.get("pe_por_presenca", 0) * atributos.get("PRE", 1)
            }

        return resultado    
    
    def _recalcular_tudo(self):
        if getattr(self, '_recalculando', False):
            return
        self._recalculando = True
        try:
            self._recalcular_totais_nex()
            self.ficha["totais_grau"] = self._calcular_totais_grau()
            bonus_passivas = self._calcular_bonus_passivas()
            bonus_skilltree = self.recalcular_bonus_skilltree()

            bonus_total = {}
            for fonte in (bonus_passivas, bonus_skilltree):
                for alvo, valor in fonte.items():
                    bonus_total[alvo] = bonus_total.get(alvo, 0) + valor

            # Bônus inato: Verdadeiro Jujutsu (exceto Restringido)
            classe = self.ficha.get("classe", "")
            if classe != "Restringido":
                # Obtém o valor numérico do Grau
                grau_str = self.ficha.get("grau", "Grau 4")
                grau_num = 0
                if "Grau" in grau_str and "Semi" not in grau_str and "Especial" not in grau_str:
                    try:
                        grau_num = int(grau_str.split()[1])
                    except:
                        pass
                elif "Semi" in grau_str:
                    grau_num = 5
                elif "Ultra" in grau_str:
                    grau_num = 7
                elif "Especial" in grau_str:
                    grau_num = 6

                lp = self.ficha.get("lp", 1)
                bonus_verdadeiro_jujutsu = grau_num + int(lp / 2)
                bonus_total["VERDADEIRO_JUJUTSU"] = bonus_total.get("VERDADEIRO_JUJUTSU", 0) + bonus_verdadeiro_jujutsu
    
            tecnicas = self.ficha.get("habilidades_tecnicas", [])
            tecnicas_ativas = self.ficha.get("tecnicas_ativas", [])
            for tecnica in tecnicas:
                if tecnica.get("tipo_mecanica") != "Passiva":
                    continue
                if tecnica["id"] not in tecnicas_ativas:
                    continue
                for efeito in tecnica.get("efeitos", []):
                    alvo = efeito["alvo"]
                    operacao = efeito["operacao"]
                    formula = efeito["formula"]

                    # Validação rápida (opcional)
                    if alvo not in ALVOS_DISPONIVEIS:
                        continue

                    try:
                        valor = avaliar_formula(formula, construir_contexto_base(self.ficha))
                    except Exception as e:
                        print(f"Erro ao avaliar efeito de técnica ({alvo}): {e}")
                        continue

                    # Obtém o valor atual do bônus (se não existir, assume 0)
                    atual = bonus_total.get(alvo, 0)

                    if operacao == '+':
                        bonus_total[alvo] = atual + valor
                    elif operacao == '-':
                        bonus_total[alvo] = atual - valor
                    elif operacao == '*':
                        # Para multiplicação, se o alvo ainda não existe, usa 1 como base
                        base = bonus_total.get(alvo, 1) if alvo in bonus_total else 1
                        bonus_total[alvo] = base * valor
                    elif operacao == '/':
                        base = bonus_total.get(alvo, 1) if alvo in bonus_total else 1
                        if valor != 0:
                            bonus_total[alvo] = base / valor
                    elif operacao == '=':
                        bonus_total[alvo] = valor

            # ══════════════════════════════════════════════════════════════════
            # Processa passivas de estilo de luta (PainelEstiloLuta)
            # ══════════════════════════════════════════════════════════════════
            habilidades_estilo = self.ficha.get("habilidades_estilo_luta", [])
            passivas_ativas = self.ficha.get("passivas_ativas", {})  # dicionário com id → "BASE"
            for hab in habilidades_estilo:
                # Apenas passivas ativadas
                if hab.get("tipo_mecanica") != "Passiva":
                    continue
                if hab["id"] not in passivas_ativas:
                    continue
                for efeito in hab.get("efeitos", []):
                    alvo = efeito["alvo"]
                    operacao = efeito["operacao"]
                    formula = efeito["formula"]

                    if alvo not in ALVOS_DISPONIVEIS:
                        continue

                    try:
                        valor = avaliar_formula(formula, construir_contexto_base(self.ficha))
                    except Exception as e:
                        print(f"Erro ao avaliar efeito de estilo de luta ({alvo}): {e}")
                        continue

                    atual = bonus_total.get(alvo, 0)

                    if operacao == '+':
                        bonus_total[alvo] = atual + valor
                    elif operacao == '-':
                        bonus_total[alvo] = atual - valor
                    elif operacao == '*':
                        base = bonus_total.get(alvo, 1) if alvo in bonus_total else 1
                        bonus_total[alvo] = base * valor
                    elif operacao == '/':
                        base = bonus_total.get(alvo, 1) if alvo in bonus_total else 1
                        if valor != 0:
                            bonus_total[alvo] = base / valor
                    elif operacao == '=':
                        bonus_total[alvo] = valor

            self.ficha["bonus_passivos"] = bonus_total
            self._salvar()
            self._atualizar_recursos_por_grau_e_nex()
            estado = self.ficha.get("estado", {})
            estado["pv_atual"] = estado.get("pv_maximo", 0)
            estado["san_atual"] = estado.get("san_maximo", 0)
            estado["pe_atual"] = estado.get("pe_maximo", 0)

            # Verifica se as barras ainda existem antes de atualizar
            for chave, barra in list(self._barras.items()):
                if barra and barra.winfo_exists():
                    if chave == "pv":
                        barra.set_valores(estado["pv_atual"], estado["pv_maximo"])
                    elif chave == "san":
                        barra.set_valores(estado["san_atual"], estado["san_maximo"])
                    elif chave == "pe":
                        barra.set_valores(estado["pe_atual"], estado["pe_maximo"])

            for painel in self._paineis_aba.values():
                if isinstance(painel, PainelResumo):
                    painel._construir()
        finally:
            self._recalculando = False

    def avaliar_dado(formula: str, contexto: dict) -> int:
        """
        Interpreta uma string como '4d6+12' ou '2d10+AB' e retorna o valor total.
        Suporta partes de dados (ex.: '4d6') e bônus que podem ser fórmulas avaliadas.
        """
        # Divide a fórmula em partes separadas por '+' ou '-'
        partes = re.split(r'(\+|-)', formula.replace(' ', ''))
        total = 0
        operador = '+'
        
        for parte in partes:
            if parte in ('+', '-'):
                operador = parte
                continue
            
            if not parte:
                continue
                
            # Verifica se é uma expressão de dado (ex.: '4d6')
            match = re.match(r'^(\d+)d(\d+)$', parte)
            if match:
                qtd = int(match.group(1))
                faces = int(match.group(2))
                valor = sum(random.randint(1, faces) for _ in range(qtd))
            else:
                # Avalia como fórmula matemática (pode conter variáveis como AB, LP)
                from ficha import avaliar_formula
                # Converte a string da parte em tokens (assumindo que é uma expressão simples)
                # Para simplificar, chamamos avaliar_formula com um token de expressão.
                # Vamos criar um token wrapper.
                tokens = _parse_expressao(parte)
                valor = avaliar_formula(tokens, contexto)
            
            if operador == '+':
                total += valor
            else:
                total -= valor
                
        return total

    def _parse_expressao(expr: str) -> list:
        """Converte uma string de expressão simples em tokens para avaliar_formula."""
        # Exemplo: "AB+5" -> [{"tipo": "variavel", "valor": "AB"}, {"tipo": "operador", "valor": "+"}, {"tipo": "constante", "valor": 5}]
        tokens = []
        i = 0
        while i < len(expr):
            char = expr[i]
            if char.isalpha():
                # Variável
                j = i
                while j < len(expr) and expr[j].isalpha():
                    j += 1
                var = expr[i:j]
                tokens.append({"tipo": "variavel", "valor": var})
                i = j
            elif char.isdigit():
                # Constante
                j = i
                while j < len(expr) and expr[j].isdigit():
                    j += 1
                num = int(expr[i:j])
                tokens.append({"tipo": "constante", "valor": num})
                i = j
            elif char in '+-*/()':
                tokens.append({"tipo": "operador", "valor": char})
                i += 1
            else:
                i += 1  # ignora caracteres estranhos
        return tokens


    def _debug_popup(self, event=None):
        """Exibe um popup com o conteúdo completo da ficha (JSON formatado) + testes de fórmula."""
        popup = ctk.CTkToplevel(self.app)
        popup.title("Debug - Ficha Completa")
        popup.geometry("700x600")
        popup.minsize(500, 400)
        popup.after(100, popup.grab_set)

        # Frame principal
        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main, text="📋 Conteúdo da ficha (JSON)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        # Caixa de texto somente leitura com scroll
        textbox = ctk.CTkTextbox(main, font=ctk.CTkFont(size=12, family="Courier"),
                                 fg_color="#1a1a1a", corner_radius=8,
                                 border_width=1, border_color="#333333",
                                 height=300)
        textbox.pack(fill="x", expand=False, pady=(0, 10))

        # Converte a ficha para JSON formatado
        dados_exibicao = {k: v for k, v in self.ficha.items() if k != "_arquivo"}
        json_str = json.dumps(dados_exibicao, indent=4, ensure_ascii=False)
        textbox.insert("1.0", json_str)
        textbox.configure(state="disabled")

        # Botão para testar fórmulas
        def testar_formulas():
            contexto = construir_contexto_base(self.ficha)
            resultados = []
            # Testes básicos
            formula1 = [{"tipo": "variavel", "valor": "LP"}, {"tipo": "operador", "valor": "*"}, {"tipo": "constante", "valor": 2}]
            r1 = avaliar_formula(formula1, contexto)
            resultados.append(f"LP * 2 = {r1}")

            formula2 = [{"tipo": "variavel", "valor": "LP"}, {"tipo": "operador", "valor": "*"},
                        {"tipo": "expressao", "valor": [{"tipo": "variavel", "valor": "AB"}, {"tipo": "operador", "valor": "/"}, {"tipo": "constante", "valor": 2}]}]
            r2 = avaliar_formula(formula2, contexto)
            resultados.append(f"LP * (AB/2) = {r2}")

            resultados.append(f"GRAU = {contexto['GRAU']}")
            resultados.append(f"NEX = {contexto['NEX']}")
            resultados.append(f"LP = {contexto['LP']}")
            resultados.append(f"AB (INT) = {contexto['AB']}")

            msg = "\n".join(resultados)
            ctk.CTkLabel(main, text=msg, font=ctk.CTkFont(size=12), justify="left").pack(pady=5)
            print(f"[DEBUG POPUP] contexto['LP'] = {contexto['LP']}")
            print(f"[DEBUG POPUP] self.ficha['lp'] = {self.ficha.get('lp')}")
            print(f"[DEBUG POPUP] self.ficha['bonus_passivos']['LP'] = {self.ficha.get('bonus_passivos', {}).get('LP')}")

        ctk.CTkButton(main, text="🧪 Testar Fórmulas (avaliar_formula)",
                      command=testar_formulas).pack(pady=5)

        # Botão fechar
        ctk.CTkButton(main, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(10, 0))
