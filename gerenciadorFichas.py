import customtkinter as ctk
import json
import os

CAMINHO_FICHAS = "data/fichas"

def carregar_fichas() -> list:
    """Lê todos os JSONs de data/fichas/ e retorna como lista."""
    fichas = []
    if not os.path.exists(CAMINHO_FICHAS):
        return fichas
    for arquivo in sorted(os.listdir(CAMINHO_FICHAS)):
        if arquivo.endswith(".json"):
            caminho = os.path.join(CAMINHO_FICHAS, arquivo)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    ficha = json.load(f)
                    ficha["_arquivo"] = caminho  # guarda o caminho pra uso futuro
                    fichas.append(ficha)
            except Exception:
                pass  # ignora arquivos corrompidos
    return fichas


class GerenciadorFichas:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Projeto BITE - Gerenciador de Fichas")
        self.app.geometry("900x600")
        self.app.minsize(700, 400)

        self.fonte_titulo     = ctk.CTkFont(size=24, weight="bold")
        self.fonte_subtitulo  = ctk.CTkFont(size=15, weight="bold")
        self.fonte_info       = ctk.CTkFont(size=13)
        self.fonte_info_label = ctk.CTkFont(size=13)
        self.fonte_botao      = ctk.CTkFont(size=14)

        self._criar_layout()
        self.app.mainloop()

    # ── Layout principal ──────────────────────────────────────────────────────

    def _criar_layout(self):
        # Cabeçalho
        header = ctk.CTkFrame(self.app, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 5))

        ctk.CTkLabel(header, text="Gerenciador de Fichas",
                     font=self.fonte_titulo).pack(side="left")

        ctk.CTkButton(header, text="↺ Atualizar", width=110,
                      font=self.fonte_botao,
                      fg_color="transparent", border_width=1,
                      command=self._recarregar).pack(side="right")

        ctk.CTkFrame(self.app, height=1,
                     fg_color="#444444").pack(fill="x", padx=20, pady=(5, 10))

        # Área de fichas
        self.area = ctk.CTkScrollableFrame(self.app, fg_color="transparent")
        self.area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._carregar_fichas()

    def _carregar_fichas(self):
        for w in self.area.winfo_children():
            w.destroy()

        fichas = carregar_fichas()

        if not fichas:
            ctk.CTkLabel(self.area,
                         text="Nenhuma ficha encontrada em data/fichas/",
                         font=self.fonte_info, text_color="gray").pack(pady=60)
            return

        for i, ficha in enumerate(fichas, start=1):
            self._card_ficha(ficha)

    def _recarregar(self):
        self._carregar_fichas()

    # ── Card de ficha ─────────────────────────────────────────────────────────

    def _card_ficha(self, ficha: dict, ):
        card = ctk.CTkFrame(self.area, corner_radius=10, border_width=1,
                            border_color="#444444", fg_color="#1e1e1e")
        card.pack(fill="x", pady=5)

        # Linha do número + nome
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=15, pady=(12, 6))


        ctk.CTkLabel(topo,
                     text=ficha.get("nome", "Sem nome"),
                     font=self.fonte_subtitulo).pack(side="left")

        if ficha.get("criado_em"):
            ctk.CTkLabel(topo,
                         text=ficha["criado_em"],
                         font=ctk.CTkFont(size=11),
                         text_color="#555555").pack(side="right")

        # Linha de informações principais
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=(0, 12))

        campos = [
            ("Classe", ficha.get("classe", "—")),
            ("Trilha",  ficha.get("trilha", "—")),
            ("NEX",     ficha.get("nex",    "—")),
            ("Grau",    ficha.get("grau",   "—")),
        ]

        for label, valor in campos:
            bloco = ctk.CTkFrame(info, fg_color="transparent")
            bloco.pack(side="left", padx=(0, 24))

            ctk.CTkLabel(bloco, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color="#888888").pack(anchor="w")
            ctk.CTkLabel(bloco, text=str(valor),
                         font=self.fonte_info).pack(anchor="w")

        # Separador + botões
        ctk.CTkFrame(card, height=1,
                     fg_color="#333333").pack(fill="x", padx=15)

        botoes = ctk.CTkFrame(card, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=8)

        ctk.CTkButton(botoes, text="Ver ficha completa", width=150,
                      font=self.fonte_botao,
                      command=lambda f=ficha: self._ver_ficha(f)).pack(side="left", padx=(0, 8))

        ctk.CTkButton(botoes, text="Excluir", width=80,
                      font=self.fonte_botao,
                      fg_color="#6b1a1a", hover_color="#4a1010",
                      command=lambda f=ficha: self._confirmar_exclusao(f)).pack(side="left")

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _ver_ficha(self, ficha: dict):
        """Abre um popup com todos os dados da ficha."""
        popup = ctk.CTkToplevel(self.app)
        popup.title(ficha.get("nome", "Ficha"))
        popup.geometry("540x600")
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text=ficha.get("nome", "—"),
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(popup, text=ficha.get("criado_em", ""),
                     font=ctk.CTkFont(size=11),
                     text_color="gray").pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        secoes = [
            ("Classe e Trilha", [
                ("Classe", ficha.get("classe", "—")),
                ("Trilha",  ficha.get("trilha",  "—")),
            ]),
            ("NEX e Grau", [
                ("NEX",   ficha.get("nex",  "—")),
                ("LP",    str(ficha.get("lp", "—"))),
                ("Grau",  ficha.get("grau", "—")),
            ]),
            ("Atributos", [
                (sigla, str(valor))
                for sigla, valor in ficha.get("atributos", {}).items()
            ]),
            ("Feitiços escolhidos", [
                (f"#{i+1}", fid)
                for i, fid in enumerate(ficha.get("feiticos", []))
            ]),
        ]

        for titulo, dados in secoes:
            if not dados:
                continue
            ctk.CTkLabel(scroll, text=titulo,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#2ecc71").pack(anchor="w", pady=(12, 4))
            for chave, valor in dados:
                linha = ctk.CTkFrame(scroll, fg_color="transparent")
                linha.pack(fill="x", pady=1)
                ctk.CTkLabel(linha, text=chave,
                             font=ctk.CTkFont(size=12),
                             text_color="#888888", width=160, anchor="w").pack(side="left")
                ctk.CTkLabel(linha, text=str(valor),
                             font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        # Skill trees — lista nós comprados por aba
        nos_comprados = ficha.get("nos_comprados", {})
        if any(nos_comprados.values()):
            ctk.CTkLabel(scroll, text="Skill Trees",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#2ecc71").pack(anchor="w", pady=(12, 4))
            for aba, nos in nos_comprados.items():
                if nos:
                    ctk.CTkLabel(scroll, text=f"  {aba}: {', '.join(nos)}",
                                 font=ctk.CTkFont(size=11),
                                 text_color="#aaaaaa").pack(anchor="w")

        ctk.CTkButton(popup, text="Fechar", width=120,
                      fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(pady=(0, 15))

    def _confirmar_exclusao(self, ficha: dict):
        popup = ctk.CTkToplevel(self.app)
        popup.title("Confirmar exclusão")
        popup.geometry("360x180")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup,
                     text=f"Excluir a ficha de\n\"{ficha.get('nome', '?')}\"?",
                     font=ctk.CTkFont(size=14), justify="center").pack(pady=(30, 20))

        botoes = ctk.CTkFrame(popup, fg_color="transparent")
        botoes.pack()

        ctk.CTkButton(botoes, text="Excluir", width=110,
                      fg_color="#6b1a1a", hover_color="#4a1010",
                      command=lambda: self._excluir_ficha(ficha, popup)).pack(side="left", padx=8)

        ctk.CTkButton(botoes, text="Cancelar", width=110,
                      fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="left", padx=8)

    def _excluir_ficha(self, ficha: dict, popup):
        caminho = ficha.get("_arquivo")
        if caminho and os.path.exists(caminho):
            os.remove(caminho)
        popup.destroy()
        self._recarregar()