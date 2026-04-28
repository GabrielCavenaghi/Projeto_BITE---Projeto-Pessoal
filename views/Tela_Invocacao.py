# views/Tela_Invocacao.py
import customtkinter as ctk
import uuid
from tkinter import messagebox
from utils.invocacao import executar_ataque_invocacao
from utils.helpers import formatar_numero_grande

class TelaInvocacao:
    """
    Janela independente com a ficha completa de uma invocação.
    Pode ser usada simultaneamente com a ficha do personagem.
    """

    ATRIBUTOS = ["AGI", "FOR", "INT", "VIG", "PRE"]

    def __init__(self, parent, inv: dict, ficha_personagem: dict, on_save=None):
        self._inv = inv
        self._ficha = ficha_personagem
        self._on_save = on_save

        self._janela = ctk.CTkToplevel(parent)
        self._janela.title(f"Invocação — {inv.get('nome', '?')}")
        self._janela.geometry("650x600")
        self._janela.minsize(500, 450)
        self._janela.resizable(True, True)
        # SEM grab_set → independente

        self._construir()

    def _construir(self):
        for w in self._janela.winfo_children():
            w.destroy()

        tabview = ctk.CTkTabview(self._janela)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tab_carac = tabview.add("Características")
        tab_acoes = tabview.add("Ações")

        self._construir_caracteristicas(tab_carac)
        self._construir_acoes(tab_acoes)

    # ══════════════════════════════════════════════════════════════════════
    # ABA CARACTERÍSTICAS
    # ══════════════════════════════════════════════════════════════════════

    def _construir_caracteristicas(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Identidade ──
        ctk.CTkLabel(scroll, text=self._inv.get("nome", "?"),
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(scroll, text=self._inv.get("grau", ""),
                     font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w")

        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a2a").pack(fill="x", pady=8)

        # ── Barra de PV interativa ──
        pv_frame = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
        pv_frame.pack(fill="x", pady=(0, 10))

        pv_header = ctk.CTkFrame(pv_frame, fg_color="transparent")
        pv_header.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(pv_header, text="Pontos de Vida",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        ctk.CTkButton(pv_header, text="✏ Editar", width=70, height=24,
              font=ctk.CTkFont(size=11),
              fg_color="transparent", border_width=1, border_color="#444444",
              command=self._popup_editar_pv).pack(side="right", padx=(0, 8))

        pv_atual = self._inv.get("pv_atual", 0)
        pv_max = self._inv.get("pv_maximo", 1)

        self._lbl_pv = ctk.CTkLabel(pv_header,
                                     text=f"{pv_atual} / {pv_max}",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#f1c40f")
        self._lbl_pv.pack(side="right")

        self._barra_pv = ctk.CTkProgressBar(pv_frame, height=14,
                                             fg_color="#333333",
                                             progress_color="#2ecc71")
        self._barra_pv.pack(fill="x", padx=10, pady=(0, 8))
        self._barra_pv.set(pv_atual / pv_max if pv_max > 0 else 0)

        # Ajuste rápido de PV
        ajuste_frame = ctk.CTkFrame(pv_frame, fg_color="transparent")
        ajuste_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._entry_pv = ctk.CTkEntry(ajuste_frame, width=70, placeholder_text="valor")
        self._entry_pv.pack(side="left", padx=(0, 6))

        ctk.CTkButton(ajuste_frame, text="− Dano", width=70, height=28,
                      fg_color="#8B0000", hover_color="#5a0000",
                      command=lambda: self._ajustar_pv(-1)).pack(side="left", padx=2)

        ctk.CTkButton(ajuste_frame, text="+ Cura", width=70, height=28,
                      fg_color="#1a5c1a", hover_color="#145214",
                      command=lambda: self._ajustar_pv(+1)).pack(side="left", padx=2)

        ctk.CTkButton(ajuste_frame, text="Definir", width=70, height=28,
                      fg_color="#2a2a5a", hover_color="#1a1a4a",
                      command=self._definir_pv).pack(side="left", padx=2)

        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a2a").pack(fill="x", pady=8)

        # ── Atributos ──
        ctk.CTkLabel(scroll, text="ATRIBUTOS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#555555").pack(anchor="w")

        attr_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        attr_grid.pack(fill="x", pady=(4, 8))

        CORES = {"AGI": "#e67e22", "FOR": "#e74c3c",
                 "INT": "#3498db", "VIG": "#2ecc71", "PRE": "#9b59b6"}

        for sigla, val in self._inv.get("atributos", {}).items():
            col = ctk.CTkFrame(attr_grid, fg_color="#1e1e1e", corner_radius=6, width=80)
            col.pack(side="left", padx=4)
            col.pack_propagate(False)
            ctk.CTkLabel(col, text=sigla, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=CORES.get(sigla, "#888888")).pack(pady=(6, 0))
            ctk.CTkLabel(col, text=str(val),
                         font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 6))

        ctk.CTkFrame(scroll, height=1, fg_color="#2a2a2a").pack(fill="x", pady=8)
        ctk.CTkButton(scroll, text="✏ Editar Atributos", width=130, height=26,
              font=ctk.CTkFont(size=11),
              fg_color="transparent", border_width=1, border_color="#444444",
              command=self._popup_editar_atributos).pack(anchor="w", pady=(6, 0))

        # ── Características customizadas ──
        header_carac = ctk.CTkFrame(scroll, fg_color="transparent")
        header_carac.pack(fill="x")

        ctk.CTkLabel(header_carac, text="CARACTERÍSTICAS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#555555").pack(side="left")

        ctk.CTkButton(header_carac, text="➕ Nova", width=80, height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color="#1a5c1a", hover_color="#145214",
                      command=self._popup_caracteristica).pack(side="right")

        caracteristicas = self._inv.setdefault("caracteristicas", [])
        if not caracteristicas:
            ctk.CTkLabel(scroll, text="Nenhuma característica adicionada.",
                         text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=8)
        else:
            for carac in caracteristicas:
                self._criar_card_caracteristica(scroll, carac)

    def _criar_card_caracteristica(self, parent, carac: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=3)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(topo, text=carac.get("nome", ""),
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        desc = carac.get("descricao", "")
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=450,
                         font=ctk.CTkFont(size=11), text_color="#aaaaaa",
                         justify="left").pack(anchor="w", padx=10, pady=(0, 4))

        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(btn_f, text="Editar", width=60, height=24,
                      fg_color="transparent", border_width=1, border_color="#444444",
                      font=ctk.CTkFont(size=11),
                      command=lambda: self._popup_caracteristica(carac)).pack(side="left", padx=(0, 4))

        ctk.CTkButton(btn_f, text="Remover", width=60, height=24,
                      fg_color="#8B0000", hover_color="#5a0000",
                      font=ctk.CTkFont(size=11),
                      command=lambda: self._remover_caracteristica(carac)).pack(side="left")

    def _popup_caracteristica(self, carac: dict = None):
        editando = carac is not None
        popup = ctk.CTkToplevel(self._janela)
        popup.title("Editar Característica" if editando else "Nova Característica")
        popup.geometry("480x320")
        popup.minsize(400, 280)
        popup.resizable(True, True)
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, carac.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(main, text="Descrição:", anchor="w").pack(fill="x")
        e_desc = ctk.CTkTextbox(main, height=120)
        if editando:
            e_desc.insert("1.0", carac.get("descricao", ""))
        e_desc.pack(fill="x", pady=(2, 12))

        btn_f = ctk.CTkFrame(main, fg_color="transparent")
        btn_f.pack(fill="x")

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Nome obrigatório.")
                return
            nova = {
                "id": carac.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "descricao": e_desc.get("1.0", "end-1c").strip()
            }
            caracs = self._inv.setdefault("caracteristicas", [])
            if editando:
                for i, c in enumerate(caracs):
                    if c.get("id") == carac.get("id"):
                        caracs[i] = nova
                        break
            else:
                caracs.append(nova)
            self._salvar()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_f, text="Salvar", fg_color="#1a6b1a",
                      command=salvar).pack(side="right", padx=(4, 0))
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                      border_width=1, command=popup.destroy).pack(side="right")

    def _remover_caracteristica(self, carac: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{carac.get('nome')}'?"):
            return
        caracs = self._inv.get("caracteristicas", [])
        self._inv["caracteristicas"] = [c for c in caracs if c.get("id") != carac.get("id")]
        self._salvar()
        self._construir()

    def _popup_editar_atributos(self):
        popup = ctk.CTkToplevel(self._janela)
        popup.title("Editar Atributos")
        popup.minsize(300, 350)
        popup.resizable(True, True)
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="Edite livremente os atributos:",
                    font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", pady=(0, 12))

        CORES = {"AGI": "#e67e22", "FOR": "#e74c3c",
                "INT": "#3498db", "VIG": "#2ecc71", "PRE": "#9b59b6"}

        entries = {}
        for sigla in self.ATRIBUTOS:
            row = ctk.CTkFrame(main, fg_color="transparent")
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(row, text=sigla, width=40,
                        font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=CORES.get(sigla, "#888888")).pack(side="left")

            e = ctk.CTkEntry(row, width=80)
            e.insert(0, str(self._inv.get("atributos", {}).get(sigla, 0)))
            e.pack(side="left", padx=(8, 0))
            entries[sigla] = e

        btn_f = ctk.CTkFrame(main, fg_color="transparent")
        btn_f.pack(fill="x", pady=(16, 0))

        def salvar():
            novos = {}
            for sigla, entry in entries.items():
                try:
                    novos[sigla] = int(entry.get())
                except ValueError:
                    messagebox.showwarning("Aviso", f"Valor inválido para {sigla}.")
                    return

            self._inv["atributos"] = novos

            # Recalcula PV se for automático
            if self._inv.get("pv_formula") == "auto":
                novo_pv = self._calcular_pv_auto()
                self._inv["pv_maximo"] = novo_pv
                self._inv["pv_atual"] = min(self._inv.get("pv_atual", novo_pv), novo_pv)

            self._salvar()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_f, text="Salvar", fg_color="#1a6b1a",
                    command=salvar).pack(side="right", padx=(4, 0))
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                    border_width=1, command=popup.destroy).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════
    # ABA AÇÕES
    # ══════════════════════════════════════════════════════════════════════

    def _construir_acoes(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(header, text="Ações",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        ctk.CTkButton(header, text="➕ Nova Ação", width=110, height=28,
                      font=ctk.CTkFont(size=11),
                      fg_color="#1a5c1a", hover_color="#145214",
                      command=self._popup_acao).pack(side="right")

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        acoes = self._inv.setdefault("acoes", [])

        atq_principal = self._inv.get("ataque_principal", {})
        if atq_principal.get("dano"):
            self._criar_card_acao(scroll, {
                "id": "__principal__",
                "nome": "Ataque Principal",
                "tipo": atq_principal.get("tipo_mecanica", "Ataque"),
                "dano": atq_principal.get("dano", ""),
                "aplicar_passo": atq_principal.get("aplicar_passo", False),
                "margem_ameaca": atq_principal.get("margem_ameaca", 20),
                "multiplicador_critico": atq_principal.get("multiplicador_critico", 2),
            }, principal=True)

        if not acoes and not atq_principal.get("dano"):
            ctk.CTkLabel(scroll, text="Nenhuma ação criada.",
                         text_color="gray").pack(pady=20)
        else:
            for acao in acoes:
                self._criar_card_acao(scroll, acao)

    def _criar_card_acao(self, parent, acao: dict, principal: bool = False):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1,
                            border_color="#444400" if principal else "#333333")
        card.pack(fill="x", pady=4)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(8, 2))

        tipo = acao.get("tipo", "Ataque")
        cor_tipo = "#e67e22" if tipo == "Ataque" else "#3498db"

        ctk.CTkLabel(topo, text=acao.get("nome", "Ação"),
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkLabel(topo, text=tipo, font=ctk.CTkFont(size=11),
                     text_color=cor_tipo).pack(side="right")

        info = f"Dano: {acao.get('dano', '—')}  |  Passo: {'Sim' if acao.get('aplicar_passo') else 'Não'}"
        if tipo == "Ataque":
            info += f"  |  {acao.get('margem_ameaca', 20)}/x{acao.get('multiplicador_critico', 2)}"
        ctk.CTkLabel(card, text=info, font=ctk.CTkFont(size=11),
                     text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(0, 4))

        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(btn_f, text="Usar", width=60, height=26,
                      fg_color="#2a6b2a", hover_color="#1a4a1a",
                      font=ctk.CTkFont(size=11),
                      command=lambda: self._usar_acao(acao)).pack(side="left", padx=(0, 4))

        if principal:
            ctk.CTkButton(btn_f, text="Editar", width=60, height=26,
                        fg_color="transparent", border_width=1, border_color="#444400",
                        font=ctk.CTkFont(size=11),
                        command=lambda: self._popup_editar_ataque_principal()).pack(side="left", padx=4)
        else:
            ctk.CTkButton(btn_f, text="Editar", width=60, height=26,
                        fg_color="transparent", border_width=1, border_color="#444444",
                        font=ctk.CTkFont(size=11),
                        command=lambda: self._popup_acao(acao)).pack(side="left", padx=4)

            ctk.CTkButton(btn_f, text="Remover", width=70, height=26,
                        fg_color="#8B0000", hover_color="#5a0000",
                        font=ctk.CTkFont(size=11),
                        command=lambda: self._remover_acao(acao)).pack(side="left", padx=4)
    
    def _popup_editar_ataque_principal(self):
        atq = self._inv.get("ataque_principal", {})

        popup = ctk.CTkToplevel(self._janela)
        popup.title("Editar Ataque Principal")
        popup.minsize(450, 380)
        popup.resizable(True, True)
        popup.after(100, popup.grab_set)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # Tipo
        ctk.CTkLabel(main, text="Tipo:", anchor="w").pack(fill="x")
        tipo_var = ctk.StringVar(value=atq.get("tipo_mecanica", "Ataque"))
        tipo_menu = ctk.CTkOptionMenu(main, values=["Ataque", "TR"], variable=tipo_var)
        tipo_menu.pack(fill="x", pady=(2, 10))

        # Dano
        ctk.CTkLabel(main, text="Dano / Efeito:", anchor="w").pack(fill="x")
        e_dano = ctk.CTkEntry(main, placeholder_text="ex: 2d8+FOR")
        e_dano.insert(0, atq.get("dano", ""))
        e_dano.pack(fill="x", pady=(2, 10))

        # Aplicar passo
        passo_var = ctk.BooleanVar(value=atq.get("aplicar_passo", False))
        ctk.CTkCheckBox(main, text="Aplicar Passo de Invocação",
                        variable=passo_var).pack(anchor="w", pady=(0, 10))

        # Margem / Multiplicador
        frame_atq = ctk.CTkFrame(main, fg_color="transparent")
        frame_atq.pack(fill="x")
        frame_atq.columnconfigure(0, weight=1)
        frame_atq.columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_atq, text="Margem de Ameaça:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        e_margem = ctk.CTkEntry(frame_atq, placeholder_text="20")
        e_margem.insert(0, str(atq.get("margem_ameaca", 20)))
        e_margem.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(frame_atq, text="Mult. Crítico:", anchor="w").grid(row=0, column=1, sticky="w")
        e_mult = ctk.CTkEntry(frame_atq, placeholder_text="2")
        e_mult.insert(0, str(atq.get("multiplicador_critico", 2)))
        e_mult.grid(row=1, column=1, sticky="ew")

        def toggle_atq(*args):
            if tipo_var.get() == "Ataque":
                frame_atq.pack(fill="x", pady=(0, 10))
            else:
                frame_atq.pack_forget()
        tipo_var.trace_add("write", toggle_atq)
        toggle_atq()

        btn_f = ctk.CTkFrame(popup, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            novo_atq = {
                "tipo_mecanica": tipo_var.get(),
                "dano": e_dano.get().strip() or "1d6",
                "aplicar_passo": passo_var.get(),
                "tipo_efeito": "invocacao",
            }
            if tipo_var.get() == "Ataque":
                try: novo_atq["margem_ameaca"] = int(e_margem.get())
                except: novo_atq["margem_ameaca"] = 20
                try: novo_atq["multiplicador_critico"] = int(e_mult.get())
                except: novo_atq["multiplicador_critico"] = 2

            self._inv["ataque_principal"] = novo_atq
            self._salvar()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_f, text="Salvar", fg_color="#1a6b1a",
                    command=salvar).pack(side="right", padx=(4, 0))
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                    border_width=1, command=popup.destroy).pack(side="right")

    def _popup_acao(self, acao: dict = None):
        editando = acao is not None
        popup = ctk.CTkToplevel(self._janela)
        popup.title("Editar Ação" if editando else "Nova Ação")
        popup.minsize(450, 400)
        popup.resizable(True, True)
        popup.after(10, lambda: popup.geometry(
            f"{min(520, popup.winfo_screenwidth()-100)}x{min(600, popup.winfo_screenheight()-100)}"
        ))
        popup.after(100, popup.grab_set)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # Nome
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, acao.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 10))

        # Tipo
        ctk.CTkLabel(main, text="Tipo:", anchor="w").pack(fill="x")
        tipo_var = ctk.StringVar(value=acao.get("tipo", "Ataque") if editando else "Ataque")
        tipo_menu = ctk.CTkOptionMenu(main, values=["Ataque", "TR"], variable=tipo_var)
        tipo_menu.pack(fill="x", pady=(2, 10))

        # Dano
        ctk.CTkLabel(main, text="Dano / Efeito:", anchor="w").pack(fill="x")
        e_dano = ctk.CTkEntry(main, placeholder_text="ex: 2d8+FOR")
        if editando:
            e_dano.insert(0, acao.get("dano", ""))
        e_dano.pack(fill="x", pady=(2, 10))

        # Aplicar passo
        passo_var = ctk.BooleanVar(value=acao.get("aplicar_passo", False) if editando else False)
        ctk.CTkCheckBox(main, text="Aplicar Passo de Invocação",
                        variable=passo_var).pack(anchor="w", pady=(0, 10))

        # Frame Ataque (margem/multiplicador)
        frame_atq = ctk.CTkFrame(main, fg_color="transparent")
        frame_atq.pack(fill="x")
        frame_atq.columnconfigure(0, weight=1)
        frame_atq.columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_atq, text="Margem de Ameaça:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        e_margem = ctk.CTkEntry(frame_atq, placeholder_text="20")
        if editando:
            e_margem.insert(0, str(acao.get("margem_ameaca", 20)))
        else:
            e_margem.insert(0, "20")
        e_margem.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(frame_atq, text="Mult. Crítico:", anchor="w").grid(row=0, column=1, sticky="w")
        e_mult = ctk.CTkEntry(frame_atq, placeholder_text="2")
        if editando:
            e_mult.insert(0, str(acao.get("multiplicador_critico", 2)))
        else:
            e_mult.insert(0, "2")
        e_mult.grid(row=1, column=1, sticky="ew")

        def toggle_atq(*args):
            if tipo_var.get() == "Ataque":
                frame_atq.pack(fill="x", pady=(0, 10))
            else:
                frame_atq.pack_forget()
        tipo_var.trace_add("write", toggle_atq)
        toggle_atq()

        # Botões
        btn_f = ctk.CTkFrame(popup, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Nome obrigatório.")
                return
            nova = {
                "id": acao.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "tipo": tipo_var.get(),
                "dano": e_dano.get().strip() or "1d6",
                "aplicar_passo": passo_var.get(),
                "tipo_efeito": "invocacao",
            }
            if tipo_var.get() == "Ataque":
                try: nova["margem_ameaca"] = int(e_margem.get())
                except: nova["margem_ameaca"] = 20
                try: nova["multiplicador_critico"] = int(e_mult.get())
                except: nova["multiplicador_critico"] = 2

            acoes = self._inv.setdefault("acoes", [])
            if editando:
                for i, a in enumerate(acoes):
                    if a.get("id") == acao.get("id"):
                        acoes[i] = nova
                        break
            else:
                acoes.append(nova)
            self._salvar()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_f, text="Salvar", fg_color="#1a6b1a",
                      command=salvar).pack(side="right", padx=(4, 0))
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                      border_width=1, command=popup.destroy).pack(side="right")

    def _usar_acao(self, acao: dict):
        resultado = executar_ataque_invocacao(self._inv, acao, self._ficha)
        self._mostrar_resultado(resultado)

    def _remover_acao(self, acao: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{acao.get('nome')}'?"):
            return
        acoes = self._inv.get("acoes", [])
        self._inv["acoes"] = [a for a in acoes if a.get("id") != acao.get("id")]
        self._salvar()
        self._construir()

    

    # ══════════════════════════════════════════════════════════════════════
    # PV
    # ══════════════════════════════════════════════════════════════════════

    def _popup_editar_pv(self):
        popup = ctk.CTkToplevel(self._janela)
        popup.title("Editar Cálculo de PV")
        popup.minsize(420, 300)
        popup.resizable(True, True)
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Tipo de fórmula
        pv_tipo_var = ctk.StringVar(
            value="auto" if self._inv.get("pv_formula") == "auto" else "custom"
        )
        ctk.CTkRadioButton(main, text="Automático (VIG * base do grau)",
                        variable=pv_tipo_var, value="auto").pack(anchor="w")
        ctk.CTkRadioButton(main, text="Fórmula customizada",
                        variable=pv_tipo_var, value="custom").pack(anchor="w", pady=(4, 10))

        ctk.CTkLabel(main, text="Fórmula (variáveis: VIG, NEX, LP_NATURAL, EA, FOR, AGI, INT, PRE):",
                    anchor="w", wraplength=380,
                    font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w")

        e_formula = ctk.CTkEntry(main, placeholder_text="VIG * 1000 + NEX * LP_NATURAL")
        formula_atual = self._inv.get("pv_formula", "auto")
        if formula_atual != "auto":
            e_formula.insert(0, formula_atual)
        e_formula.pack(fill="x", pady=(4, 6))

        # PV máximo atual (apenas leitura)
        lbl_preview = ctk.CTkLabel(main, text=f"PV Máximo atual: {self._inv.get('pv_maximo', 0)}",
                                    font=ctk.CTkFont(size=12), text_color="#f1c40f")
        lbl_preview.pack(anchor="w", pady=(0, 12))

        def toggle_formula(*args):
            if pv_tipo_var.get() == "custom":
                e_formula.configure(state="normal")
            else:
                e_formula.configure(state="disabled")
        pv_tipo_var.trace_add("write", toggle_formula)
        toggle_formula()

        def preview():
            """Calcula e mostra o PV resultante sem salvar."""
            if pv_tipo_var.get() == "auto":
                from views.Painel_Invocacao import PainelInvocacao
                # Instancia temporária só para usar o método de cálculo
                pv = self._calcular_pv_auto()
            else:
                pv = self._calcular_pv_custom(e_formula.get().strip())
            lbl_preview.configure(text=f"PV Máximo resultante: {pv}")

        ctk.CTkButton(main, text="👁 Pré-visualizar", height=28,
                    fg_color="transparent", border_width=1,
                    command=preview).pack(fill="x", pady=(0, 10))

        btn_f = ctk.CTkFrame(main, fg_color="transparent")
        btn_f.pack(fill="x")

        def salvar():
            if pv_tipo_var.get() == "auto":
                nova_formula = "auto"
                novo_pv = self._calcular_pv_auto()
            else:
                nova_formula = e_formula.get().strip() or "auto"
                novo_pv = self._calcular_pv_custom(nova_formula)

            self._inv["pv_formula"] = nova_formula
            self._inv["pv_maximo"] = novo_pv
            self._inv["pv_atual"] = min(self._inv.get("pv_atual", novo_pv), novo_pv)
            self._salvar()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_f, text="Salvar", fg_color="#1a6b1a",
                    command=salvar).pack(side="right", padx=(4, 0))
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                    border_width=1, command=popup.destroy).pack(side="right")
        
    def _calcular_pv_auto(self) -> int:
        import os, json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "invocacoes.json")
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)["graus"].get(self._inv.get("grau", "Grau 4"), {})

        from utils.Efeitos_Scalling import string_para_tokens
        from ficha import avaliar_formula
        vig = self._inv.get("atributos", {}).get("VIG", 1)
        ctx_local = {"VIG": vig}
        try:
            tokens = string_para_tokens(dados.get("vida_formula", "VIG*100"))
            pv = int(avaliar_formula(tokens, ctx_local))
        except:
            pv = vig * 100
        return pv + dados.get("vida_bonus_por_vig", 0) * vig

    def _calcular_pv_custom(self, formula_str: str) -> int:
        from ficha import construir_contexto_base, avaliar_formula
        from utils.Efeitos_Scalling import string_para_tokens
        ctx = construir_contexto_base(self._ficha)
        for sigla, val in self._inv.get("atributos", {}).items():
            ctx[sigla] = val
        try:
            tokens = string_para_tokens(formula_str)
            return int(avaliar_formula(tokens, ctx))
        except Exception as e:
            print(f"Erro PV custom: {e}")
            return 100

    def _ajustar_pv(self, sinal: int):
        texto = self._entry_pv.get().strip()
        if not texto:
            return
        try:
            valor = int(texto)
        except ValueError:
            return
        pv_max = self._inv.get("pv_maximo", 1)
        novo = max(0, min(self._inv.get("pv_atual", 0) + valor * sinal, pv_max))
        self._inv["pv_atual"] = novo
        self._lbl_pv.configure(text=f"{novo} / {pv_max}")
        self._barra_pv.set(novo / pv_max if pv_max > 0 else 0)
        self._salvar()

    def _definir_pv(self):
        texto = self._entry_pv.get().strip()
        if not texto:
            return
        try:
            valor = int(texto)
        except ValueError:
            return
        pv_max = self._inv.get("pv_maximo", 1)
        novo = max(0, min(valor, pv_max))
        self._inv["pv_atual"] = novo
        self._lbl_pv.configure(text=f"{novo} / {pv_max}")
        self._barra_pv.set(novo / pv_max if pv_max > 0 else 0)
        self._salvar()

    
    # ══════════════════════════════════════════════════════════════════════
    # RESULTADO
    # ══════════════════════════════════════════════════════════════════════

    def _mostrar_resultado(self, resultado: dict):
        popup = ctk.CTkToplevel(self._janela)
        popup.title("Resultado")
        popup.geometry("420x280")
        popup.resizable(True, True)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        dano = resultado.get("detalhes", {}).get("dano", 0)
        texto = resultado.get("mensagem", "")
        if dano and dano > 9999:
            texto = texto.replace(str(dano), formatar_numero_grande(dano))

        ctk.CTkLabel(main, text=texto, wraplength=370,
                     justify="left", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 20))
        ctk.CTkButton(main, text="Fechar", command=popup.destroy).pack()

    # ══════════════════════════════════════════════════════════════════════
    # PERSISTÊNCIA
    # ══════════════════════════════════════════════════════════════════════

    def _salvar(self):
        if self._on_save:
            self._on_save()