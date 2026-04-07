import customtkinter as ctk
import json
import os
from ficha import FichaPersonagem

CAMINHO_FICHAS = "data/fichas"

def carregar_fichas() -> list:
    fichas = []
    if not os.path.exists(CAMINHO_FICHAS):
        return fichas
    for arquivo in sorted(os.listdir(CAMINHO_FICHAS)):
        if arquivo.endswith(".json"):
            caminho = os.path.join(CAMINHO_FICHAS, arquivo)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    ficha = json.load(f)
                    ficha["_arquivo"] = caminho
                    fichas.append(ficha)
            except Exception:
                pass
    return fichas


class GerenciadorFichas:
    def __init__(self, parent, on_voltar_para_main=None):
        """
        parent: janela principal (CTk) que será usada como pai da Toplevel
        on_voltar_para_main: callback chamado ao clicar em Voltar
        """
        self.parent = parent
        self.on_voltar_para_main = on_voltar_para_main

        # Cria uma janela filha (Toplevel) – NÃO uma nova CTk!
        self.janela = ctk.CTkToplevel(parent)
        self.janela.title("Projeto BITE - Gerenciador de Fichas")
        self.janela.geometry("900x600")
        self.janela.minsize(700, 400)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar_janela)  # trata o X

        self.fonte_titulo = ctk.CTkFont(size=24, weight="bold")
        self.fonte_subtitulo = ctk.CTkFont(size=15, weight="bold")
        self.fonte_info = ctk.CTkFont(size=13)
        self.fonte_botao = ctk.CTkFont(size=14)

        self._criar_layout()

    def _fechar_janela(self):
        """Quando o usuário fechar a janela, chama o callback de voltar (se existir)"""
        if self.on_voltar_para_main:
            self.on_voltar_para_main()
        self.janela.destroy()

    def _criar_layout(self):
        # Limpa o conteúdo da Toplevel (caso esteja sendo recriada)
        for widget in self.janela.winfo_children():
            widget.destroy()

        main_frame = ctk.CTkFrame(self.janela, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Botão Voltar
        if self.on_voltar_para_main:
            ctk.CTkButton(main_frame, text="← Voltar", font=self.fonte_botao,
                          command=self._voltar, width=100).pack(anchor="nw", pady=(0, 10))

        # Cabeçalho
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header, text="Gerenciador de Fichas",
                     font=self.fonte_titulo).pack(side="left")
        ctk.CTkButton(header, text="↺ Atualizar", width=110,
                      font=self.fonte_botao, fg_color="transparent",
                      border_width=1, command=self._recarregar).pack(side="right")

        ctk.CTkFrame(main_frame, height=1,
                     fg_color="#444444").pack(fill="x", pady=(5, 10))

        self.area = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.area.pack(fill="both", expand=True)

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

        for ficha in fichas:
            self._card_ficha(ficha)

    def _recarregar(self):
        self._carregar_fichas()

    def _card_ficha(self, ficha: dict):
        card = ctk.CTkFrame(self.area, corner_radius=10, border_width=1,
                            border_color="#444444", fg_color="#1e1e1e")
        card.pack(fill="x", pady=5)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=15, pady=(12, 6))
        ctk.CTkLabel(topo, text=ficha.get("nome", "Sem nome"),
                     font=self.fonte_subtitulo).pack(side="left")
        if ficha.get("criado_em"):
            ctk.CTkLabel(topo, text=ficha["criado_em"],
                         font=ctk.CTkFont(size=11),
                         text_color="#555555").pack(side="right")

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=(0, 12))
        campos = [
            ("Classe", ficha.get("classe", "—")),
            ("Trilha", ficha.get("trilha", "—")),
            ("NEX",    ficha.get("nex",    "—")),
            ("Grau",   ficha.get("grau",   "—")),
        ]
        for label, valor in campos:
            bloco = ctk.CTkFrame(info, fg_color="transparent")
            bloco.pack(side="left", padx=(0, 24))
            ctk.CTkLabel(bloco, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color="#888888").pack(anchor="w")
            ctk.CTkLabel(bloco, text=str(valor),
                         font=self.fonte_info).pack(anchor="w")

        ctk.CTkFrame(card, height=1, fg_color="#333333").pack(fill="x", padx=15)

        botoes = ctk.CTkFrame(card, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=8)
        ctk.CTkButton(botoes, text="Abrir Ficha", width=150,
                      font=self.fonte_botao,
                      command=lambda f=ficha: self._ver_ficha(f)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(botoes, text="Excluir", width=80,
                      font=self.fonte_botao, fg_color="#6b1a1a", hover_color="#4a1010",
                      command=lambda f=ficha: self._confirmar_exclusao(f)).pack(side="left")

    def _ver_ficha(self, ficha: dict):
        """Abre a ficha na mesma janela (Toplevel) – igual ao FichaPersonagem original"""
        def voltar_ao_gerenciador():
            # Reconstrói o gerenciador na mesma Toplevel
            self._criar_layout()

        # O FichaPersonagem recebe a janela (self.janela) e reconstrói o conteúdo
        FichaPersonagem(self.janela, ficha, on_voltar=voltar_ao_gerenciador)

    def _confirmar_exclusao(self, ficha: dict):
        popup = ctk.CTkToplevel(self.janela)
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

    def _voltar(self):
        """Botão Voltar: fecha a Toplevel e chama o callback para reexibir a main"""
        if self.on_voltar_para_main:
            self.on_voltar_para_main()
        self.janela.destroy()