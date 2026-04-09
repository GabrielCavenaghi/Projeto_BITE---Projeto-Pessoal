import customtkinter as ctk
import json
import os

from views.Painel_EditorSkilltree import EditorSkilltree


class PainelSkilltree(ctk.CTkFrame):
    """Aba: nós de skill tree comprados, agrupados por atributo, com detalhes ao clicar."""

    CAMINHO_SKILLTREE = "data/skilltrees.json"

    CORES = {
        "AGI": "#e67e22", "FOR": "#e74c3c", "INT": "#3498db",
        "VIG": "#2ecc71", "PRE": "#9b59b6", "GERAL": "#95a5a6",
    }

    def __init__(self, parent, ficha: dict, on_change=None, **kwargs):
        kwargs.pop('on_change', None)
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_change = on_change
        self._db = self._carregar_db()
        self._construir()

    def _carregar_db(self) -> dict:
        db = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_json = os.path.join(base_dir, "data", "skilltrees.json")
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for atributo, conteudo in data.items():
                        for no in conteudo.get("nos", []):
                            db[no["id"]] = no
            except Exception as e:
                print(f"Erro ao carregar skilltree: {e}")
        else:
            print(f"Arquivo não encontrado: {caminho_json}")
        return db

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        nos_comprados = self._ficha.get("nos_comprados", {})

        if not any(nos_comprados.values()):
            ctk.CTkLabel(self, text="Nenhuma perícia comprada ainda.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Ordem de exibição dos atributos
        ordem_atributos = ["AGI", "FOR", "INT", "VIG", "PRE", "GERAL"]

        for aba in ordem_atributos:
            nos = nos_comprados.get(aba, [])
            if not nos:
                continue
            cor = self.CORES.get(aba, "#888888")

            # Cabeçalho da seção
            header = ctk.CTkFrame(scroll, fg_color="transparent")
            header.pack(fill="x", pady=(12, 4))

            ctk.CTkFrame(header, width=4, height=16,
                         fg_color=cor, corner_radius=2).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(header, text=aba,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=cor).pack(side="left")
            ctk.CTkLabel(header, text=f"{len(nos)} nós",
                         font=ctk.CTkFont(size=11),
                         text_color="#555555").pack(side="right")

            # Cards dos nós
            for no_id in nos:
                dados_no = self._db.get(no_id, {"id": no_id, "nome": no_id, "descricao": ""})
                self._criar_card(scroll, dados_no, aba)

        btn_editar = ctk.CTkButton(
            self, text="✎ Editar Skill Tree", width=150, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_editor
        )    
        btn_editar.pack(anchor="ne", padx=10, pady=(5, 0))

        # Scroll com roda do mouse
        def _scroll(delta):
            scroll._parent_canvas.yview_scroll(delta, "units")
        def _bind_scroll_recursivo(widget):
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)
        _bind_scroll_recursivo(scroll)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))
        scroll.focus_set()

    def _abrir_editor(self):
        # Importa a classe EditorSkilltree (definida abaixo)
        editor = EditorSkilltree(self.winfo_toplevel(), self._ficha, on_close=self._on_editor_close)
        editor.abrir()
        self._on_change       

    def _on_editor_close(self):
        # Quando o editor é fechado com sucesso, atualiza a visualização
        self.atualizar()
        # Dispara recálculo de bônus (via callback se existir)
        if hasattr(self, '_on_change') and self._on_change:
            self._on_change()

    def _tornar_clicavel(self, widget, callback):
        widget.bind("<Button-1>", lambda e: callback())
        for child in widget.winfo_children():
            self._tornar_clicavel(child, callback)

    def _criar_card(self, parent, dados_no: dict, atributo: str):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e",
                            corner_radius=6, border_width=1,
                            border_color="#333333")
        card.pack(fill="x", pady=2, padx=2)

        self._tornar_clicavel(card, lambda: self._mostrar_detalhes(dados_no, atributo))

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(topo, text=dados_no.get("nome", dados_no.get("id", "?")),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        ctk.CTkLabel(topo, text=dados_no.get("id", ""),
                     font=ctk.CTkFont(size=10),
                     text_color="#555555").pack(side="right")

        desc = dados_no.get("descricao", "")
        if desc:
            previa = (desc[:50] + "…") if len(desc) > 50 else desc
            ctk.CTkLabel(card, text=previa, wraplength=480, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#888888").pack(anchor="w", padx=10, pady=(0, 8))

    def _mostrar_detalhes(self, dados_no: dict, atributo: str):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(dados_no.get("nome", dados_no.get("id", "Perícia")))
        popup.geometry("500x400")
        popup.minsize(400, 300)
        popup.after(100, popup.grab_set)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        nome = dados_no.get("nome", dados_no.get("id", "???"))
        ctk.CTkLabel(scroll, text=nome,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 4))

        cor_attr = self.CORES.get(atributo, "#888888")
        ctk.CTkLabel(scroll, text=f"Atributo: {atributo}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=cor_attr).pack(anchor="w", pady=(0, 12))

        desc = dados_no.get("descricao", "Sem descrição disponível.")
        frame_desc = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
        frame_desc.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_desc, text="📜 Descrição",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cccccc").pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(frame_desc, text=desc, wraplength=440, justify="left",
                     font=ctk.CTkFont(size=12),
                     text_color="#bbbbbb").pack(anchor="w", padx=12, pady=(0, 12))

        requisitos = dados_no.get("requisitos", [])
        if requisitos:
            req_text = ", ".join(requisitos)
            ctk.CTkLabel(scroll, text=f"🔗 Requisitos: {req_text}",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", pady=(4, 8))

        custo = dados_no.get("custo")
        if custo is not None:
            ctk.CTkLabel(scroll, text=f"💰 Custo: {custo} ponto(s)",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(popup, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(0, 8))

    def atualizar(self):
        self._db = self._carregar_db()
        self._construir()
