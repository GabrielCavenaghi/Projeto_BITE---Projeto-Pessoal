import customtkinter as ctk
from utils.progressao import calcular_totais_ate_nex
from utils.atributos import (atributos_iniciais, calcular_pontos_disponiveis,
                              ajustar_atributo, atributos_validos, adicionar_pontos_extras)
from utils.skilltree import (
    carregar_skilltrees, pontos_disponiveis_skilltree,
    pode_comprar, vender_no, tem_filhos_comprados
)
import json
import os

# ══════════════════════════════════════════════════════════════════════════════
# Carregamento de dados
# ══════════════════════════════════════════════════════════════════════════════

CAMINHO_CLASSES = "data/classes.json"

def carregar_classes():
    if not os.path.exists(CAMINHO_CLASSES):
        dados_padrao = [{
            "nome": "Guerreiro", "descricao": "Classe combatente corpo a corpo.",
            "trilha": ["Guerreiro Clássico"], "descricaoTrilha": ["Descrição padrão"],
            "habilidadeTrilha": [[]], "descricaoHabilidadeTrilha": [[]]
        }]
        with open(CAMINHO_CLASSES, "w", encoding="utf-8") as f:
            json.dump(dados_padrao, f, indent=4, ensure_ascii=False)
        return dados_padrao
    with open(CAMINHO_CLASSES, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# Classe principal
# ══════════════════════════════════════════════════════════════════════════════

class CriadorFichas:

    ATRIBUTOS_SIGLAS = ["AGI", "FOR", "INT", "VIG", "PRE"]

    def __init__(self, on_voltar_para_main=None):
        self.app = ctk.CTk()
        self.app.title("Projeto BITE - Criador de Fichas")
        self.app.geometry("1200x800")
        self.app.minsize(900, 600)

        self.on_voltar_para_main = on_voltar_para_main
        self.classes             = carregar_classes()

        # ── Estado do personagem (preenchido conforme o usuário avança) ──────
        self.classe_selecionada  = None
        self.trilha_selecionada  = None
        self.nex_selecionado     = None
        self.lp_selecionado      = None
        self.totais_nex          = None
        self.grau_selecionado    = None
        self.pontos_extras_grau  = 0
        self.habilidades_trilha  = []
        self.atributos           = None
        self.pontos_disponiveis  = 0

        # ── Estado da skill tree ────────────────────────────────────────────
        self.nos_comprados       = {}
        self.pontos_skilltree    = {}
        self.abas_confirmadas    = set()
        self.no_selecionado      = None
        self.aba_skilltree_ativa = "INT"

        # ── Estado de confirmação ───────────────────────────────────────────
        self.nome_personagem = ""
        self._secoes_expandidas = {}

        # ── Estado dos feitiços ─────────────────────────────────────────────
        self.feiticos_escolhidos  = []   # lista de ids escolhidos
        self.pontos_feiticos      = 0    # calculado pelo NEX
        self.aba_feitico_ativa    = None

        # ── Fontes centralizadas ─────────────────────────────────────────────
        self.fonte_titulo      = ctk.CTkFont(size=32, weight="bold")
        self.fonte_card_titulo = ctk.CTkFont(size=22, weight="bold")
        self.fonte_card_desc   = ctk.CTkFont(size=16)
        self.fonte_hab_titulo  = ctk.CTkFont(size=15, weight="bold")
        self.fonte_hab_desc    = ctk.CTkFont(size=13)
        self.fonte_botao       = ctk.CTkFont(size=18)

        # ── Dimensões dos cards ──────────────────────────────────────────────
        self.card_w_classe = 300
        self.card_h_classe = 480
        self.card_w_trilha = 360
        self.card_h_trilha = 620

        self._criar_frames()
        self._mostrar_classes()
        self.app.mainloop()

    # ══════════════════════════════════════════════════════════════════════════
    # Infraestrutura: frames e navegação
    # ══════════════════════════════════════════════════════════════════════════

    def _criar_frames(self):
        self.main = ctk.CTkFrame(self.app, fg_color="transparent")
        self.main.pack(fill="both", expand=True, padx=20, pady=20)

        self.frame_classe      = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_trilha      = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_nex         = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_grau        = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_atributos   = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_skilltree   = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_feiticos    = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_confirmacao = ctk.CTkFrame(self.main, fg_color="transparent")

        self.todos_frames = [
            self.frame_classe, self.frame_trilha, self.frame_nex, self.frame_grau,
            self.frame_atributos, self.frame_skilltree,
            self.frame_feiticos, self.frame_confirmacao
        ]

    def mostrar_aba(self, frame):
        for f in self.todos_frames:
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers de layout reutilizáveis
    # ══════════════════════════════════════════════════════════════════════════

    def _btn_voltar(self, parent, comando):
        ctk.CTkButton(parent, text="← Voltar", font=self.fonte_botao,
                      command=comando, width=100).pack(anchor="nw", padx=10, pady=10)

    def _titulo(self, parent, texto):
        ctk.CTkLabel(parent, text=texto,
                     font=self.fonte_titulo).pack(pady=(20, 10))

    def _separador(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color="#444444").pack(fill="x", padx=20, pady=5)

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 1 — Escolha de Classe
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_classes(self):
        for w in self.frame_classe.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_classe, self._voltar_para_main)
        self._titulo(self.frame_classe, "Escolha sua Classe")

        carrossel = ctk.CTkScrollableFrame(self.frame_classe, orientation="horizontal",
                                           height=self.card_h_classe + 20,
                                           fg_color="transparent")
        carrossel.pack(fill="both", expand=True, padx=20, pady=10)

        for classe in self.classes:
            self._card_classe(classe, carrossel)

        self.mostrar_aba(self.frame_classe)

    def _card_classe(self, classe, parent):
        card = ctk.CTkFrame(parent, width=self.card_w_classe, height=self.card_h_classe,
                            corner_radius=15, border_width=2,
                            border_color="#555555", fg_color="#2b2b2b")
        card.pack(side="left", padx=15, pady=10)
        card.pack_propagate(False)

        # Nome da classe
        ctk.CTkLabel(card, text=classe["nome"],
                    font=self.fonte_card_titulo).pack(pady=(20, 10))

        # Frame rolável para a descrição (vertical)
        desc_frame = ctk.CTkScrollableFrame(card, orientation="vertical",
                                            fg_color="transparent")
        desc_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Label da descrição dentro do frame rolável
        ctk.CTkLabel(desc_frame, text=classe["descricao"],
                    wraplength=self.card_w_classe - 40, justify="center",
                    font=self.fonte_card_desc).pack(pady=5, padx=5, fill="both", expand=True)

        # Botão de escolha
        ctk.CTkButton(card, text="Escolher Classe", font=self.fonte_botao,
                    command=lambda c=classe: self._escolher_classe(c)).pack(pady=20)

    def _escolher_classe(self, classe):
        self.classe_selecionada = classe
        self._mostrar_trilhas()

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 2 — Escolha de Trilha
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_trilhas(self):
        for w in self.frame_trilha.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_trilha, self._mostrar_classes)
        self._titulo(self.frame_trilha, f"Trilhas de {self.classe_selecionada['nome']}")

        carrossel = ctk.CTkScrollableFrame(self.frame_trilha, orientation="horizontal",
                                           fg_color="transparent")
        carrossel.pack(fill="both", expand=True, padx=20, pady=10)

        c = self.classe_selecionada
        trilhas     = c.get("trilha",                    ["Trilha Única"])
        descricoes  = c.get("descricaoTrilha",           ["Sem descrição disponível"])
        habilidades = c.get("habilidadeTrilha",          [[]])
        desc_hab    = c.get("descricaoHabilidadeTrilha", [[]])

        for i, (trilha, desc) in enumerate(zip(trilhas, descricoes)):
            self._card_trilha(
                trilha, desc,
                habilidades[i] if i < len(habilidades) else [],
                desc_hab[i]    if i < len(desc_hab)    else [],
                carrossel
            )

        self.mostrar_aba(self.frame_trilha)

    def _card_trilha(self, nome, descricao, habilidades, desc_habilidades, parent):
        card = ctk.CTkFrame(parent, width=self.card_w_trilha, height=self.card_h_trilha,
                            corner_radius=15, border_width=2,
                            border_color="#555555", fg_color="#2b2b2b")
        card.pack(side="left", padx=15, pady=10)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=nome,
                     font=self.fonte_card_titulo).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=descricao, wraplength=self.card_w_trilha - 40,
                     justify="center", font=self.fonte_card_desc).pack(pady=(5, 10), padx=10)

        ctk.CTkFrame(card, height=2, fg_color="#555555").pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(card, text="Habilidades da Trilha",
                     font=self.fonte_hab_titulo).pack(pady=(5, 5))

        btn = ctk.CTkButton(card, text="Escolher Trilha", font=self.fonte_botao,
                            command=lambda t=nome, h=habilidades: self._escolher_trilha(t, h),
                            height=45, corner_radius=10)
        btn.pack(side="bottom", pady=(10, 15), padx=20, fill="x")

        hab_frame = ctk.CTkScrollableFrame(card, orientation="vertical",
                                           fg_color="#1a1a1a", corner_radius=10)
        hab_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        niveis = ["10%", "40%", "65%", "99%"]
        for i, hab_nome in enumerate(habilidades[:4]):
            hab_desc = desc_habilidades[i] if i < len(desc_habilidades) else "Sem descrição."
            nivel    = niveis[i] if i < len(niveis) else ""

            hab_card = ctk.CTkFrame(hab_frame, corner_radius=8,
                                    fg_color="#2b2b2b", border_width=1,
                                    border_color="#444444")
            hab_card.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(hab_card, text=f"[{nivel}] {hab_nome}",
                         font=self.fonte_hab_titulo, anchor="w").pack(pady=(8,3), padx=8, anchor="w")
            ctk.CTkLabel(hab_card, text=hab_desc,
                         wraplength=self.card_w_trilha - 60, justify="left",
                         font=self.fonte_hab_desc, text_color="#cccccc").pack(pady=(0,8), padx=8, fill="x")

    def _escolher_trilha(self, trilha, habilidades):
        self.trilha_selecionada = trilha
        self.habilidades_trilha = habilidades
        self._mostrar_nex()

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 3 — Escolha de NEX
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_nex(self):
        for w in self.frame_nex.winfo_children():
            w.destroy()

        self.valores_nex = (
            [f"{i}%" for i in range(5, 96, 5)] +
            ["99%"] +
            [f"{i/10:.1f}%" for i in range(991, 1000)] +
            ["99.99%"]
        )

        self.frame_nex.grid_rowconfigure(0, weight=1)
        self.frame_nex.grid_rowconfigure(1, weight=0)
        self.frame_nex.grid_rowconfigure(2, weight=1)
        self.frame_nex.grid_columnconfigure(0, weight=1)

        btn_voltar = ctk.CTkButton(self.frame_nex, text="← Voltar", font=self.fonte_botao,
                                   command=self._mostrar_trilhas, width=100)
        btn_voltar.place(x=10, y=10)

        ctk.CTkLabel(self.frame_nex, text="Escolha o NEX do Personagem",
                     font=self.fonte_titulo).grid(row=0, column=0, sticky="s", pady=(50, 20))

        centro = ctk.CTkFrame(self.frame_nex, fg_color="transparent")
        centro.grid(row=1, column=0, sticky="ew", padx=60)

        self.nex_label = ctk.CTkLabel(centro, text=self.valores_nex[0],
                                      font=ctk.CTkFont(size=48, weight="bold"))
        self.nex_label.pack(pady=(0, 4))

        self.lp_label = ctk.CTkLabel(centro, text="", font=self.fonte_card_desc,
                                     text_color="gray")
        self.lp_label.pack(pady=(0, 20))

        self.slider_nex = ctk.CTkSlider(
            centro, from_=0, to=len(self.valores_nex) - 1,
            number_of_steps=len(self.valores_nex) - 1,
            command=self._ao_mover_slider
        )
        self.slider_nex.set(0)
        self.slider_nex.pack(fill="x", pady=(0, 8))

        extremos = ctk.CTkFrame(centro, fg_color="transparent")
        extremos.pack(fill="x")
        ctk.CTkLabel(extremos, text="5%",
                     font=self.fonte_hab_desc, text_color="gray").pack(side="left")
        ctk.CTkLabel(extremos, text="99.99%",
                     font=self.fonte_hab_desc, text_color="gray").pack(side="right")

        ctk.CTkButton(centro, text="Próximo →", font=self.fonte_botao,
                      command=self._confirmar_nex, width=150).pack(pady=30)

        self._atualizar_lp()
        self.mostrar_aba(self.frame_nex)

    def _ao_mover_slider(self, valor):
        indice  = round(valor)
        nex_str = self.valores_nex[indice]
        self.nex_label.configure(text=nex_str)
        self.lp_label.configure(text=f"Limite de PE (LP): {self._calcular_lp(nex_str)}")

    def _atualizar_lp(self):
        indice  = round(self.slider_nex.get()) if hasattr(self, "slider_nex") else 0
        nex_str = self.valores_nex[indice]
        self.nex_label.configure(text=nex_str)
        self.lp_label.configure(text=f"Limite de PE (LP): {self._calcular_lp(nex_str)}")

    def _calcular_lp(self, nex_str):
        try:
            nex = float(nex_str.replace("%", "").replace(",", "."))
        except ValueError:
            return 0
        if abs(nex - 99.99) < 0.01: return 30
        if nex == 99:                return 20
        if nex == 50:                return 10
        if 5 <= nex <= 95 and nex % 5 == 0:
            return int(nex // 5)
        if 99.1 <= nex <= 99.9:
            return int(round(20 + (nex - 99) * (10 / 0.99)))
        return 0

    def _confirmar_nex(self):
        indice               = round(self.slider_nex.get())
        self.nex_selecionado = self.valores_nex[indice]
        self.lp_selecionado  = self._calcular_lp(self.nex_selecionado)
        self.totais_nex      = calcular_totais_ate_nex(self.nex_selecionado)
        self._mostrar_grau()

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 4 — Escolha de Grau
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_grau(self):
        from utils.graus import carregar_graus, listar_graus, extras_do_grau
        for w in self.frame_grau.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_grau, self._mostrar_nex)
        self._titulo(self.frame_grau, "Escolha o Grau do Personagem")

        graus_data  = carregar_graus()
        graus_lista = listar_graus(graus_data)

        descricoes = {
            "Grau 4":             "PV -2/NEX • SAN -3/NEX • PE -1/NEX",
            "Grau 3":             "PV base • SAN base • PE base",
            "Grau 2":             "PV +2/NEX • SAN +1/NEX • PE +1/NEX",
            "Grau 1":             "PV +2/NEX • SAN +3/NEX • PE +2/NEX",
            "Grau Semi Especial": "PV +5/NEX • SAN +7/NEX • PE +5/NEX\nVigor Impressionante • Estamina Excelente",
            "Grau Especial":      "PV/PE/SAN pela classe • Vigor Superior\nEstamina Sobrenatural • +1 Ponto de Atributo",
            "Grau Ultra Especial":"PV/PE/SAN pela classe • Vigor Ultra Superior\nEstamina Ultra Sobrenatural • +1 Ponto de Atributo",
        }

        scroll = ctk.CTkScrollableFrame(self.frame_grau, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        grade = ctk.CTkFrame(scroll, fg_color="transparent")
        grade.pack(expand=True, pady=10)

        colunas = 4
        for i, nome_grau in enumerate(graus_lista):
            linha  = i // colunas
            coluna = i % colunas

            card = ctk.CTkFrame(grade, corner_radius=12, border_width=2,
                                border_color="#555555", fg_color="#2b2b2b",
                                width=220, height=160)
            card.grid(row=linha * 2, column=coluna, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            grade.columnconfigure(coluna, weight=1)

            ctk.CTkLabel(card, text=nome_grau,
                         font=self.fonte_hab_titulo).pack(pady=(15, 6), padx=10)
            ctk.CTkLabel(card, text=descricoes.get(nome_grau, ""),
                         font=ctk.CTkFont(size=12), text_color="#aaaaaa",
                         wraplength=190, justify="center").pack(padx=10, fill="both", expand=True)

            extras     = extras_do_grau(nome_grau, graus_data)
            extras_txt = (f"+{extras['graus_treinamento']} Grau Treino • "
                          f"+{extras['encantamentos']} Enc. • "
                          f"+{extras['maldicoes']} Maldições")
            if extras.get("pontos_atributo"):
                extras_txt += f" • +{extras['pontos_atributo']} Atributo"

            ctk.CTkLabel(card, text=extras_txt,
                         font=ctk.CTkFont(size=11), text_color="#666666",
                         wraplength=190, justify="center").pack(padx=10, pady=(0, 10))

            ctk.CTkButton(grade, text=f"Escolher {nome_grau}",
                          font=self.fonte_hab_desc,
                          command=lambda g=nome_grau, d=graus_data: self._escolher_grau(g, d)
                          ).grid(row=linha * 2 + 1, column=coluna, padx=10, pady=(0, 15), sticky="ew")

        self.mostrar_aba(self.frame_grau)

    def _escolher_grau(self, nome_grau, graus_data):
        from utils.graus import extras_do_grau
        self.grau_selecionado   = nome_grau
        extras                  = extras_do_grau(nome_grau, graus_data)
        self.pontos_extras_grau = extras.get("pontos_atributo", 0)
        self._mostrar_atributos()

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 5 — Distribuição de Atributos
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_atributos(self):
        for w in self.frame_atributos.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_atributos, self._mostrar_grau)
        self.pontos_disponiveis = calcular_pontos_disponiveis(self.totais_nex) + self.pontos_extras_grau
        self.atributos          = atributos_iniciais()

        self.canvas = ctk.CTkCanvas(self.frame_atributos, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._desenhar_atributos())
        self._desenhar_atributos()

        # Painel de pontos extras
        extras_frame = ctk.CTkFrame(self.frame_atributos, fg_color="transparent")
        extras_frame.pack(pady=(0, 5))

        ctk.CTkLabel(extras_frame, text="Pontos extras (buffs):",
                     font=self.fonte_hab_desc, text_color="gray").pack(side="left", padx=(0, 10))
        self.entrada_extras = ctk.CTkEntry(extras_frame, width=60, justify="center",
                                           placeholder_text="0")
        self.entrada_extras.pack(side="left", padx=(0, 8))
        ctk.CTkButton(extras_frame, text="Adicionar", width=100,
                      font=self.fonte_hab_desc,
                      command=self._adicionar_pontos_extras).pack(side="left")
        self.label_extras_erro = ctk.CTkLabel(extras_frame, text="",
                                              font=self.fonte_hab_desc, text_color="#e74c3c")
        self.label_extras_erro.pack(side="left", padx=(10, 0))

        ctk.CTkButton(self.frame_atributos, text="Confirmar Atributos →",
                      font=self.fonte_botao,
                      command=self._confirmar_atributos).pack(pady=15)

        self.mostrar_aba(self.frame_atributos)

    def _desenhar_atributos(self):
        import math
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy   = w // 2, h // 2
        raio_orb = min(w, h) // 8
        dist     = min(w, h) // 3

        posicoes = {"AGI": -90, "FOR": -90+72, "VIG": -90+144,
                    "PRE": -90-144, "INT": -90-72}

        coords = {}
        for sigla, ang in posicoes.items():
            rad = math.radians(ang)
            coords[sigla] = (cx + dist * math.cos(rad), cy + dist * math.sin(rad))

        for ax, ay in coords.values():
            self.canvas.create_line(cx, cy, ax, ay, fill="#555555", width=2)

        r = raio_orb * 1.1
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                fill="#2b2b2b", outline="#888888", width=2)
        self.canvas.create_text(cx, cy - 12, text="ATRIBUTOS",
                                fill="white", font=("Arial", int(raio_orb * 0.28), "bold"))
        self.canvas.create_text(cx, cy + 12, fill="#aaaaaa",
                                text=f"{self.pontos_disponiveis} pts disponíveis",
                                font=("Arial", int(raio_orb * 0.22)))

        for sigla, (ax, ay) in coords.items():
            self._desenhar_circulo_atributo(sigla, ax, ay, raio_orb)

    def _desenhar_circulo_atributo(self, sigla, ax, ay, r):
        attr = self.atributos[sigla]
        self.canvas.create_oval(ax-r, ay-r, ax+r, ay+r,
                                fill="#2b2b2b", outline="#888888", width=2)
        self.canvas.create_text(ax, ay - r*0.22, text=str(attr["valor"]),
                                fill="white", font=("Arial", int(r*0.38), "bold"))
        self.canvas.create_text(ax, ay + r*0.12, text=attr["nome"],
                                fill="#aaaaaa", font=("Arial", int(r*0.17)))
        self.canvas.create_text(ax, ay + r*0.42, text=sigla,
                                fill="white", font=("Arial", int(r*0.30), "bold"))

        tamanho_btn = max(int(r * 0.35), 20)
        btn_menos = ctk.CTkButton(self.canvas, text="-", width=tamanho_btn,
                                  height=tamanho_btn, font=ctk.CTkFont(size=14),
                                  command=lambda s=sigla: self._ajustar_atributo(s, -1))
        btn_mais  = ctk.CTkButton(self.canvas, text="+", width=tamanho_btn,
                                  height=tamanho_btn, font=ctk.CTkFont(size=14),
                                  command=lambda s=sigla: self._ajustar_atributo(s, +1))
        self.canvas.create_window(ax - r*0.45, ay + r*0.75, window=btn_menos)
        self.canvas.create_window(ax + r*0.45, ay + r*0.75, window=btn_mais)

    def _ajustar_atributo(self, sigla, delta):
        resultado = ajustar_atributo(self.atributos, sigla, delta, self.pontos_disponiveis)
        if resultado is None:
            return
        self.atributos, self.pontos_disponiveis = resultado
        self._desenhar_atributos()

    def _adicionar_pontos_extras(self):
        texto = self.entrada_extras.get().strip()
        try:
            quantidade = int(texto)
        except ValueError:
            self.label_extras_erro.configure(text="Digite um número válido.")
            return
        if quantidade <= 0:
            self.label_extras_erro.configure(text="Digite um valor maior que 0.")
            return
        self.label_extras_erro.configure(text="")
        self.pontos_disponiveis = adicionar_pontos_extras(self.pontos_disponiveis, quantidade)
        self.entrada_extras.delete(0, "end")
        self._desenhar_atributos()

    def _confirmar_atributos(self):
        if not atributos_validos(self.pontos_disponiveis):
            print(f"Ainda tem {self.pontos_disponiveis} pontos pra distribuir!")
            return
        self._mostrar_skilltree()

    # ══════════════════════════════════════════════════════════════════════════
    # Tela 6 — Skill Trees
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_skilltree(self):
        for w in self.frame_skilltree.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_skilltree, self._mostrar_atributos)
        self._titulo(self.frame_skilltree, "Skill Trees")

        # Inicializa estado
        for sigla in self.ATRIBUTOS_SIGLAS:
            if sigla not in self.nos_comprados:
                self.nos_comprados[sigla] = set()
            if sigla not in self.pontos_skilltree:
                self.pontos_skilltree[sigla] = pontos_disponiveis_skilltree(
                    self.atributos[sigla]["valor"])

        if "GERAL" not in self.nos_comprados:
            self.nos_comprados["GERAL"] = set()

        self.abas_confirmadas    = set()
        self.skilltrees_data     = carregar_skilltrees()
        self.aba_skilltree_ativa = "INT"

        # ── Tabs ─────────────────────────────────────────────────────────────
        tabs_frame = ctk.CTkFrame(self.frame_skilltree, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=20, pady=(0, 5))

        self.tab_botoes = {}
        for aba in self.ATRIBUTOS_SIGLAS + ["GERAL"]:
            btn = ctk.CTkButton(tabs_frame, text=aba, width=90,
                                font=self.fonte_hab_titulo,
                                command=lambda a=aba: self._trocar_aba_skilltree(a))
            btn.pack(side="left", padx=4)
            self.tab_botoes[aba] = btn

        self.tab_botoes["GERAL"].configure(state="disabled", fg_color="#333333")

        # ── Container do canvas ──────────────────────────────────────────────
        self.st_container = ctk.CTkFrame(self.frame_skilltree, fg_color="transparent")
        self.st_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        self.st_pontos_label = ctk.CTkLabel(self.st_container, text="",
                                            font=self.fonte_card_desc)
        self.st_pontos_label.pack(anchor="e", padx=10, pady=(5, 0))

        canvas_frame = ctk.CTkFrame(self.st_container, fg_color="transparent")
        canvas_frame.pack(fill="both", expand=True)

        self.st_canvas = ctk.CTkCanvas(canvas_frame, bg="#1a1a1a", highlightthickness=0)
        scroll_x = ctk.CTkScrollbar(canvas_frame, orientation="horizontal",
                                    command=self.st_canvas.xview)
        scroll_y = ctk.CTkScrollbar(canvas_frame, orientation="vertical",
                                    command=self.st_canvas.yview)

        self.st_canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        self.st_canvas.pack(side="left", fill="both", expand=True)

        self.st_canvas.bind("<Button-4>", lambda e: self.st_canvas.yview_scroll(-1, "units"))
        self.st_canvas.bind("<Button-5>", lambda e: self.st_canvas.yview_scroll( 1, "units"))
        self.st_canvas.bind("<MouseWheel>",
                            lambda e: self.st_canvas.yview_scroll(-1*(e.delta//120), "units"))
        self.st_canvas.bind("<Shift-MouseWheel>",
                            lambda e: self.st_canvas.xview_scroll(-1*(e.delta//120), "units"))
        self.st_canvas.bind("<Configure>", lambda e: self._desenhar_skilltree())

        # ── Botões do rodapé ─────────────────────────────────────────────────
        rodape = ctk.CTkFrame(self.frame_skilltree, fg_color="transparent")
        rodape.pack(fill="x", padx=20, pady=(0, 10))

        self.btn_confirmar_aba = ctk.CTkButton(
            rodape, text="Confirmar esta Skill Tree →",
            font=self.fonte_hab_desc, fg_color="#1a4a6b", hover_color="#123450",
            command=self._confirmar_aba_skilltree)
        self.btn_confirmar_aba.pack(side="left", padx=(0, 10))

        self.btn_reset = ctk.CTkButton(
            rodape, text="Resetar Skill Trees",
            font=self.fonte_hab_desc, fg_color="#8B0000", hover_color="#5a0000",
            command=self._resetar_skilltree)
        self.btn_reset.pack(side="left", padx=(0, 10))

        self.btn_avancar = ctk.CTkButton(
            rodape, text="Confirmar tudo e avançar →",
            font=self.fonte_botao, state="disabled", fg_color="#333333",
            command=self._confirmar_skilltrees)
        self.btn_avancar.pack(side="left")

        self.mostrar_aba(self.frame_skilltree)
        self._trocar_aba_skilltree("INT")

    def _trocar_aba_skilltree(self, aba):
        if aba == "GERAL" and not self._todas_abas_confirmadas():
            faltando = [s for s in self.ATRIBUTOS_SIGLAS if s not in self.abas_confirmadas]
            self.st_canvas.delete("all")
            w = self.st_canvas.winfo_width()
            h = self.st_canvas.winfo_height()
            self.st_canvas.create_text(
                w//2, h//2 - 20,
                text="Confirme todas as skill trees de atributo antes de acessar a GERAL.",
                fill="#e67e22", font=("Arial", 13), width=w - 40)
            self.st_canvas.create_text(
                w//2, h//2 + 20,
                text=f"Faltando: {', '.join(faltando)}",
                fill="#888888", font=("Arial", 11))
            return

        self.aba_skilltree_ativa = aba

        # Atualiza visual dos botões de tab
        for sigla, btn in self.tab_botoes.items():
            if sigla == aba:
                btn.configure(fg_color=("green4", "#1a6b1a"))
            elif sigla in self.abas_confirmadas:
                btn.configure(fg_color=("#145214", "#0a3d0a"))
            elif sigla == "GERAL" and not self._todas_abas_confirmadas():
                btn.configure(fg_color="#333333")
            else:
                btn.configure(fg_color=("gray75", "gray25"))

        # Inicializa os pontos da GERAL quando ela for aberta pela primeira vez
        if aba == "GERAL" and self._todas_abas_confirmadas():
            self.pontos_skilltree["GERAL"] = sum(
                self.pontos_skilltree[sigla] for sigla in self.ATRIBUTOS_SIGLAS
            )
            for sigla in self.ATRIBUTOS_SIGLAS:
                self.pontos_skilltree[sigla] = 0

        # Mostra/esconde botão de confirmar aba
        if aba == "GERAL" or aba in self.abas_confirmadas:
            self.btn_confirmar_aba.pack_forget()
        else:
            self.btn_confirmar_aba.pack(side="left", padx=(0, 10))

        self._desenhar_skilltree()

    def _confirmar_aba_skilltree(self):
        aba = self.aba_skilltree_ativa
        if aba == "GERAL" or aba in self.abas_confirmadas:
            return

        self.abas_confirmadas.add(aba)
        self._recalcular_pontos_gerais()

        if self._todas_abas_confirmadas():
            self.tab_botoes["GERAL"].configure(state="normal")
            self.btn_avancar.configure(state="normal", fg_color=("#1a5c1a", "#1a5c1a"))

        self._trocar_aba_skilltree(aba)

    def _todas_abas_confirmadas(self) -> bool:
        return all(s in self.abas_confirmadas for s in self.ATRIBUTOS_SIGLAS)

    def _recalcular_pontos_gerais(self):
        if not self._todas_abas_confirmadas():
            self.pontos_skilltree["GERAL"] = sum(
                pts for sigla, pts in self.pontos_skilltree.items()
                if sigla != "GERAL"
            )

    def _desenhar_skilltree(self):
        from utils.skilltree import calcular_posicoes

        self.st_canvas.delete("all")
        aba       = self.aba_skilltree_ativa
        nos       = self.skilltrees_data.get(aba, {}).get("nos", [])
        pontos    = self.pontos_skilltree.get(aba, 0)
        comprados = self.nos_comprados.get(aba, set())

        self.st_pontos_label.configure(text=f"Pontos disponíveis em {aba}: {pontos}")

        if not nos:
            w = self.st_canvas.winfo_width()
            h = self.st_canvas.winfo_height()
            self.st_canvas.create_text(w//2, h//2, text="Nenhum nó disponível ainda.",
                                       fill="#555555", font=("Arial", 16))
            self.st_canvas.configure(scrollregion=(0, 0, w, h))
            return

        posicoes_grid = calcular_posicoes(nos)
        no_r    = 36
        padding = 5
        espaco  = no_r * 2 + padding
        margem  = no_r + 10

        max_col   = max(c for c, l in posicoes_grid.values())
        max_linha = max(l for c, l in posicoes_grid.values())
        canvas_w  = max(margem * 2 + espaco * (max_col + 1),   self.st_canvas.winfo_width())
        canvas_h  = max(margem * 2 + espaco * (max_linha + 1), self.st_canvas.winfo_height())

        self.st_posicoes = {}
        for no_id, (col, linha) in posicoes_grid.items():
            self.st_posicoes[no_id] = (margem + espaco * col + no_r,
                                       margem + espaco * linha + no_r)

        self.st_canvas.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        # Linhas de requisito
        for no in nos:
            if no["id"] not in self.st_posicoes:
                continue
            x2, y2 = self.st_posicoes[no["id"]]
            for req_id in no["requisitos"]:
                if req_id in self.st_posicoes:
                    x1, y1 = self.st_posicoes[req_id]
                    cor = "#4a7a4a" if req_id in comprados else "#444444"
                    self.st_canvas.create_line(x1, y1, x2, y2, fill=cor, width=2)

        # Nós
        for no in nos:
            if no["id"] not in self.st_posicoes:
                continue
            x, y       = self.st_posicoes[no["id"]]
            comprado   = no["id"] in comprados
            disponivel = pode_comprar(no, comprados, pontos)

            if comprado:
                cor_fill, cor_borda, cor_texto = "#7a6000", "#FFD700", "#FFD700"
            elif disponivel:
                cor_fill, cor_borda, cor_texto = "#1a4a1a", "#2ecc71", "#2ecc71"
            else:
                cor_fill, cor_borda, cor_texto = "#2b2b2b", "#555555", "#555555"

            self.st_canvas.create_oval(x-no_r, y-no_r, x+no_r, y+no_r,
                                       fill=cor_fill, outline=cor_borda, width=2,
                                       tags=(no["id"], "no"))
            nome_curto = no["nome"][:14] + "…" if len(no["nome"]) > 14 else no["nome"]
            self.st_canvas.create_text(x, y - 8, text=nome_curto,
                                       fill=cor_texto, font=("Arial", 9, "bold"),
                                       width=no_r * 1.8, tags=(no["id"], "no"))
            self.st_canvas.create_text(x, y + 12, text=f"{no['custo']}pt",
                                       fill=cor_texto, font=("Arial", 8),
                                       tags=(no["id"], "no"))
            self.st_canvas.tag_bind(no["id"], "<Button-1>",
                                    lambda e, n=no: self._abrir_popup_no(n))

    def _abrir_popup_no(self, no):
        from utils.skilltree import pode_comprar, tem_filhos_comprados

        aba        = self.aba_skilltree_ativa
        comprados  = self.nos_comprados.get(aba, set())
        pontos     = self.pontos_skilltree.get(aba, 0)
        comprado   = no["id"] in comprados
        disponivel = pode_comprar(no, comprados, pontos) if not comprado else False

        popup = ctk.CTkToplevel(self.app)
        popup.title(no["nome"])
        popup.geometry("440x420")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text=no["nome"],
                     font=self.fonte_card_titulo).pack(pady=(20, 5), padx=20)
        ctk.CTkLabel(popup, text=f"Custo: {no['custo']} ponto(s)",
                     font=self.fonte_hab_desc, text_color="gray").pack(pady=(0, 8))
        ctk.CTkLabel(popup, text=no["descricao"],
                     font=self.fonte_hab_desc, wraplength=380,
                     justify="center").pack(pady=(0, 12), padx=20, fill="both", expand=True)

        if no["requisitos"]:
            nos_por_id = {n["id"]: n for n in self.skilltrees_data[aba]["nos"]}
            nomes_req  = [nos_por_id[r]["nome"] for r in no["requisitos"] if r in nos_por_id]
            ctk.CTkLabel(popup, text=f"Requer: {', '.join(nomes_req)}",
                         font=ctk.CTkFont(size=12), text_color="#e67e22",
                         wraplength=380).pack(pady=(0, 12), padx=20)

        self._separador(popup)

        if comprado:
            ctk.CTkLabel(popup, text="✓ Já comprado",
                         text_color="#FFD700", font=self.fonte_hab_titulo).pack(pady=8)
            # Verifica se tem filhos comprados antes de permitir venda
            tem_filhos = tem_filhos_comprados(no["id"], self.skilltrees_data[aba]["nos"], comprados)
            if tem_filhos:
                ctk.CTkLabel(popup, text="⚠ Não pode vender: há habilidades que dependem deste nó.",
                             text_color="#e74c3c", font=ctk.CTkFont(size=11)).pack(pady=4)
            else:
                ctk.CTkButton(popup, text=f"Vender (recupera {no['custo']} pt)",
                              font=self.fonte_botao, fg_color="#8B0000", hover_color="#5a0000",
                              height=40,
                              command=lambda: self._vender_no(no, popup)).pack(pady=8, padx=40, fill="x")
        elif disponivel:
            ctk.CTkButton(popup, text=f"Comprar  •  {no['custo']} pt",
                          font=self.fonte_botao, fg_color="#1a6b1a", hover_color="#145214",
                          height=40,
                          command=lambda: self._comprar_no(no, popup)).pack(pady=8, padx=40, fill="x")
        else:
            motivo = "Pontos insuficientes" if no["custo"] > pontos else "Requisitos não atendidos"
            ctk.CTkLabel(popup, text=f"🔒 Bloqueado — {motivo}",
                         text_color="#888888", font=ctk.CTkFont(size=12)).pack(pady=8)

        ctk.CTkButton(popup, text="Fechar", width=120,
                      fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(pady=(4, 16))

    def _comprar_no(self, no, popup):
        aba = self.aba_skilltree_ativa
        self.nos_comprados[aba].add(no["id"])
        self.pontos_skilltree[aba] -= no["custo"]
        if aba != "GERAL":
            self._recalcular_pontos_gerais()
        popup.destroy()
        self._desenhar_skilltree()

    def _vender_no(self, no, popup):
        aba = self.aba_skilltree_ativa
        comprados = self.nos_comprados[aba]
        if no["id"] in comprados:
            comprados.remove(no["id"])
            self.pontos_skilltree[aba] += no["custo"]
            if aba != "GERAL":
                self._recalcular_pontos_gerais()
        popup.destroy()
        self._desenhar_skilltree()

    def _resetar_skilltree(self):
        """Reseta completamente a skill tree: remove todos os nós comprados, restaura pontos iniciais e desconfirma abas."""
        from utils.skilltree import pontos_disponiveis_skilltree

        # Reinicia estado das árvores de atributo
        for sigla in self.ATRIBUTOS_SIGLAS:
            self.nos_comprados[sigla] = set()
            self.pontos_skilltree[sigla] = pontos_disponiveis_skilltree(self.atributos[sigla]["valor"])

        self.nos_comprados["GERAL"] = set()
        self.pontos_skilltree["GERAL"] = 0

        # Limpa as abas confirmadas
        self.abas_confirmadas.clear()

        # Rebloqueia a aba GERAL e o botão avançar
        self.tab_botoes["GERAL"].configure(state="disabled", fg_color="#333333")
        self.btn_avancar.configure(state="disabled", fg_color="#333333")

        # Volta para a primeira aba (INT)
        self._trocar_aba_skilltree("INT")

    def _confirmar_skilltrees(self):
        self._mostrar_feiticos()


    # ══════════════════════════════════════════════════════════════════════════════
    # Tela 7 — Feitiços
    # ══════════════════════════════════════════════════════════════════════════════

    def _mostrar_feiticos(self):
        from utils.feiticos import carregar_feiticos, feiticos_por_classe, abas_disponiveis

        for w in self.frame_feiticos.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_feiticos, self._mostrar_skilltree)
        self.feiticos_data    = carregar_feiticos()
        self.feiticos_por_aba = feiticos_por_classe(self.feiticos_data)

        # Pontos de feitiço vêm do totais_nex
        self.pontos_feiticos = self.totais_nex.get("feiticos", 0)

        # Cabeçalho com contador
        header = ctk.CTkFrame(self.frame_feiticos, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(header, text="Feitiços",
                    font=self.fonte_titulo).pack(side="left")

        self.feiticos_contador = ctk.CTkLabel(
            header, text=self._texto_contador_feiticos(),
            font=self.fonte_card_desc, text_color="gray")
        self.feiticos_contador.pack(side="right", padx=10)

        # Tabs
        tabs_frame = ctk.CTkFrame(self.frame_feiticos, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=20, pady=(0, 5))

        classe_personagem = self.classe_selecionada["nome"]
        self.abas_feiticos = abas_disponiveis(self.feiticos_data, classe_personagem)
        self.tab_feitico_botoes = {}

        for aba in self.abas_feiticos:
            btn = ctk.CTkButton(tabs_frame, text=aba, width=120,
                                font=self.fonte_hab_desc,
                                command=lambda a=aba: self._trocar_aba_feitico(a))
            btn.pack(side="left", padx=4)
            self.tab_feitico_botoes[aba] = btn

        # Container da lista
        self.feitico_container = ctk.CTkFrame(self.frame_feiticos, fg_color="transparent")
        self.feitico_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        ctk.CTkButton(self.frame_feiticos, text="Confirmar Feitiços →",
                    font=self.fonte_botao,
                    command=self._confirmar_feiticos).pack(pady=10)

        self.mostrar_aba(self.frame_feiticos)
        self._trocar_aba_feitico(self.abas_feiticos[0])

    def _texto_contador_feiticos(self) -> str:
        return f"Feitiços: {len(self.feiticos_escolhidos)} / {self.pontos_feiticos}"

    def _trocar_aba_feitico(self, aba):
        self.aba_feitico_ativa = aba
        for nome, btn in self.tab_feitico_botoes.items():
            btn.configure(fg_color=("green4", "#1a6b1a") if nome == aba
                        else ("gray75", "gray25"))
        self._desenhar_lista_feiticos()

    def _desenhar_lista_feiticos(self):
        for w in self.feitico_container.winfo_children():
            w.destroy()

        aba      = self.aba_feitico_ativa
        feiticos = self.feiticos_por_aba.get(aba, [])

        scroll = ctk.CTkScrollableFrame(self.feitico_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not feiticos:
            ctk.CTkLabel(scroll, text="Nenhum feitiço disponível nesta aba.",
                        text_color="gray", font=self.fonte_hab_desc).pack(pady=40)
            return

        for feitico in feiticos:
            self._card_feitico(feitico, scroll)

    def _card_feitico(self, feitico, parent):
        escolhido  = feitico["id"] in self.feiticos_escolhidos
        pode_pegar = (len(self.feiticos_escolhidos) < self.pontos_feiticos
                    and not escolhido)

        if escolhido:
            cor_borda, cor_bg = "#FFD700", "#3a3000"
        elif pode_pegar:
            cor_borda, cor_bg = "#2ecc71", "#1a2b1a"
        else:
            cor_borda, cor_bg = "#555555", "#2b2b2b"

        card = ctk.CTkFrame(parent, corner_radius=10, border_width=2,
                            border_color=cor_borda, fg_color=cor_bg)
        card.pack(fill="x", padx=5, pady=4)

        # Linha superior: nome + grau + status
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(topo, text=feitico["nome"],
                    font=self.fonte_hab_titulo).pack(side="left")

        grau_txt = f"Grau {feitico['grau_base']}" if isinstance(feitico['grau_base'], int) else feitico['grau_base']
        ctk.CTkLabel(topo, text=grau_txt,
                    font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(side="left", padx=8)

        if escolhido:
            ctk.CTkLabel(topo, text="✓ Escolhido",
                        text_color="#FFD700", font=ctk.CTkFont(size=12)).pack(side="right")

        # Descrição resumida
        desc_curta = feitico["descricao_base"][:120] + "…" \
                    if len(feitico["descricao_base"]) > 120 else feitico["descricao_base"]
        ctk.CTkLabel(card, text=desc_curta, wraplength=700, justify="left",
                    text_color="#cccccc", font=self.fonte_hab_desc).pack(
                        anchor="w", padx=12, pady=(0, 8))

        # Botão de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Ver detalhes", width=110,
                    font=self.fonte_hab_desc, fg_color="transparent",
                    border_width=1,
                    command=lambda f=feitico: self._abrir_popup_feitico(f)).pack(side="left")

        if escolhido:
            ctk.CTkButton(btn_frame, text="Desistir", width=100,
                        font=self.fonte_hab_desc, fg_color="#6b1a1a",
                        hover_color="#4a1010",
                        command=lambda f=feitico: self._desistir_feitico(f)).pack(side="left", padx=(8, 0))
        elif pode_pegar:
            ctk.CTkButton(btn_frame, text="Escolher", width=100,
                        font=self.fonte_hab_desc, fg_color="#1a6b1a",
                        hover_color="#145214",
                        command=lambda f=feitico: self._escolher_feitico(f)).pack(side="left", padx=(8, 0))

    def _abrir_popup_feitico(self, feitico):
        from utils.feiticos import versoes_disponiveis

        popup = ctk.CTkToplevel(self.app)
        popup.title(feitico["nome"])
        popup.geometry("520x500")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        # Cabeçalho
        ctk.CTkLabel(popup, text=feitico["nome"],
                    font=self.fonte_card_titulo).pack(pady=(20, 2), padx=20)

        grau_txt = f"Grau base: {feitico['grau_base']} • Classe: {feitico['classe']}"
        ctk.CTkLabel(popup, text=grau_txt,
                    font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 10))

        self._separador(popup)

        # Conteúdo scrollável
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Descrição base
        ctk.CTkLabel(scroll, text="Versão base (Grau 4):",
                    font=self.fonte_hab_titulo, text_color="#aaaaaa").pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text=feitico["descricao_base"],
                    font=self.fonte_hab_desc, wraplength=460,
                    justify="left").pack(anchor="w", pady=(0, 12))

        # Versões desbloqueadas pelo grau do personagem
        versoes = versoes_disponiveis(feitico, self.grau_selecionado)
        if versoes:
            self._separador(scroll)
            ctk.CTkLabel(scroll, text="Versões desbloqueadas pelo seu grau:",
                        font=self.fonte_hab_titulo, text_color="#2ecc71").pack(anchor="w", pady=(8, 4))

            for v in versoes:
                desc_versao = feitico["versoes"][v]
                ctk.CTkLabel(scroll, text=v,
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="#FFD700").pack(anchor="w", pady=(6, 2))
                ctk.CTkLabel(scroll, text=desc_versao,
                            font=self.fonte_hab_desc, wraplength=460,
                            justify="left", text_color="#dddddd").pack(anchor="w", pady=(0, 6))

        self._separador(popup)

        # Botões
        escolhido  = feitico["id"] in self.feiticos_escolhidos
        pode_pegar = len(self.feiticos_escolhidos) < self.pontos_feiticos and not escolhido

        botoes = ctk.CTkFrame(popup, fg_color="transparent")
        botoes.pack(pady=(5, 15))

        if escolhido:
            ctk.CTkButton(botoes, text="Desistir deste feitiço",
                        fg_color="#6b1a1a", hover_color="#4a1010",
                        font=self.fonte_hab_desc,
                        command=lambda: [self._desistir_feitico(feitico), popup.destroy()]
                        ).pack(side="left", padx=5)
        elif pode_pegar:
            ctk.CTkButton(botoes, text="Escolher este feitiço",
                        fg_color="#1a6b1a", hover_color="#145214",
                        font=self.fonte_hab_desc,
                        command=lambda: [self._escolher_feitico(feitico), popup.destroy()]
                        ).pack(side="left", padx=5)
        else:
            ctk.CTkLabel(botoes,
                        text="Sem pontos disponíveis" if not escolhido else "",
                        text_color="#888888", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)

        ctk.CTkButton(botoes, text="Fechar", width=100,
                    fg_color="transparent", border_width=1,
                    command=popup.destroy).pack(side="left", padx=5)

    def _escolher_feitico(self, feitico):
        if (feitico["id"] not in self.feiticos_escolhidos and
                len(self.feiticos_escolhidos) < self.pontos_feiticos):
            self.feiticos_escolhidos.append(feitico["id"])
            self._atualizar_contador_feiticos()
            self._desenhar_lista_feiticos()

    def _desistir_feitico(self, feitico):
        if feitico["id"] in self.feiticos_escolhidos:
            self.feiticos_escolhidos.remove(feitico["id"])
            self._atualizar_contador_feiticos()
            self._desenhar_lista_feiticos()

    def _atualizar_contador_feiticos(self):
        self.feiticos_contador.configure(text=self._texto_contador_feiticos())

    def _confirmar_feiticos(self):
        self._mostrar_confirmacao()

    # ══════════════════════════════════════════════════════════════════════════════
    # Tela 8 — Confirmação e salvamento
    # ══════════════════════════════════════════════════════════════════════════════

    def _mostrar_confirmacao(self):
        for w in self.frame_confirmacao.winfo_children():
            w.destroy()

        self._btn_voltar(self.frame_confirmacao, self._mostrar_feiticos)
        self._titulo(self.frame_confirmacao, "Confirmar Ficha")

        # Campo de nome
        nome_frame = ctk.CTkFrame(self.frame_confirmacao, fg_color="transparent")
        nome_frame.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(nome_frame, text="Nome do Personagem:",
                    font=self.fonte_hab_titulo).pack(side="left", padx=(0, 10))
        self.entrada_nome = ctk.CTkEntry(nome_frame, width=300,
                                        placeholder_text="Digite o nome...",
                                        font=self.fonte_card_desc)
        self.entrada_nome.pack(side="left")
        if self.nome_personagem:
            self.entrada_nome.insert(0, self.nome_personagem)

        # Scroll principal
        scroll = ctk.CTkScrollableFrame(self.frame_confirmacao, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Seções colapsáveis
        secoes = [
            ("Classe e Trilha",  self._conteudo_secao_classe),
            ("NEX e Grau",       self._conteudo_secao_nex),
            ("Atributos",        self._conteudo_secao_atributos),
            ("Skill Trees",      self._conteudo_secao_skilltrees),
            ("Feitiços",         self._conteudo_secao_feiticos),
        ]

        for titulo, construtor in secoes:
            self._secao_colapsavel(scroll, titulo, construtor)

        # Botão confirmar
        ctk.CTkButton(self.frame_confirmacao,
                    text="Salvar Ficha ✓",
                    font=self.fonte_botao,
                    fg_color="#1a6b1a", hover_color="#145214",
                    height=45,
                    command=self._salvar_ficha).pack(pady=12)

        self.mostrar_aba(self.frame_confirmacao)

    def _secao_colapsavel(self, parent, titulo, construtor_conteudo):
        """Cria uma seção com cabeçalho clicável que expande/colapsa o conteúdo."""
        expandida = self._secoes_expandidas.get(titulo, False)

        container = ctk.CTkFrame(parent, corner_radius=10, border_width=1,
                                border_color="#444444", fg_color="#1e1e1e")
        container.pack(fill="x", padx=5, pady=5)

        # Cabeçalho clicável
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x")

        seta_var = ctk.StringVar(value="▼" if expandida else "▶")

        seta = ctk.CTkLabel(header, textvariable=seta_var,
                            font=ctk.CTkFont(size=14), width=24)
        seta.pack(side="left", padx=(12, 4), pady=12)

        ctk.CTkLabel(header, text=titulo,
                    font=self.fonte_hab_titulo).pack(side="left", pady=12)

        # Botão editar
        destino = {
            "Classe e Trilha": self._mostrar_classes,
            "NEX e Grau":      self._mostrar_nex,
            "Atributos":       self._mostrar_atributos,
            "Skill Trees":     self._mostrar_skilltree,
            "Feitiços":        self._mostrar_feiticos,
        }
        if titulo in destino:
            ctk.CTkButton(header, text="✎ Editar", width=80,
                        font=ctk.CTkFont(size=12),
                        fg_color="transparent", border_width=1,
                        command=destino[titulo]).pack(side="right", padx=12, pady=8)

        # Frame de conteúdo
        conteudo_frame = ctk.CTkFrame(container, fg_color="transparent")

        def toggle():
            atual = self._secoes_expandidas.get(titulo, False)
            self._secoes_expandidas[titulo] = not atual
            if not atual:
                seta_var.set("▼")
                construtor_conteudo(conteudo_frame)
                conteudo_frame.pack(fill="x", padx=15, pady=(0, 12))
            else:
                seta_var.set("▶")
                conteudo_frame.pack_forget()
                for w in conteudo_frame.winfo_children():
                    w.destroy()

        # Bind no header inteiro
        for widget in [header, seta]:
            widget.bind("<Button-1>", lambda e: toggle())

        ctk.CTkButton(header, text="", width=0, fg_color="transparent",
                    command=toggle, hover=False).pack(side="left", fill="x", expand=True)

        if expandida:
            construtor_conteudo(conteudo_frame)
            conteudo_frame.pack(fill="x", padx=15, pady=(0, 12))

    # ── Construtores de conteúdo de cada seção ────────────────────────────────────

    def _conteudo_secao_classe(self, parent):
        dados = [
            ("Classe",  self.classe_selecionada["nome"] if self.classe_selecionada else "—"),
            ("Trilha",  self.trilha_selecionada or "—"),
        ]
        self._tabela_info(parent, dados)

    def _conteudo_secao_nex(self, parent):
        dados = [
            ("NEX",             self.nex_selecionado or "—"),
            ("LP",              str(self.lp_selecionado or "—")),
            ("Grau",            self.grau_selecionado or "—"),
        ]
        if self.totais_nex:
            dados += [
                ("Pontos de Atributo (NEX)", str(self.totais_nex.get("pontos_atributo", 0))),
                ("Feitiços (NEX)",           str(self.totais_nex.get("feiticos", 0))),
                ("Graus de Treinamento",     str(self.totais_nex.get("graus_treinamento", 0))),
                ("Habilidades de Trilha",    str(self.totais_nex.get("habilidade_trilha", 0))),
            ]
        self._tabela_info(parent, dados)

    def _conteudo_secao_atributos(self, parent):
        if not self.atributos:
            ctk.CTkLabel(parent, text="Nenhum atributo distribuído.",
                        text_color="gray").pack()
            return
        dados = [(f"{d['nome']} ({s})", str(d["valor"]))
                for s, d in self.atributos.items()]
        self._tabela_info(parent, dados)

    def _conteudo_secao_skilltrees(self, parent):
        if not self.nos_comprados:
            ctk.CTkLabel(parent, text="Nenhum nó comprado.",
                        text_color="gray").pack()
            return

        for aba, nos in self.nos_comprados.items():
            if not nos:
                continue

            ctk.CTkLabel(parent, text=aba,
                        font=self.fonte_hab_titulo,
                        text_color="#2ecc71").pack(anchor="w", pady=(8, 2))

            # Busca nomes dos nós
            nos_por_id = {n["id"]: n
                        for n in self.skilltrees_data.get(aba, {}).get("nos", [])}
            for no_id in nos:
                no = nos_por_id.get(no_id)
                if no:
                    ctk.CTkLabel(parent,
                                text=f"  • {no['nome']} ({no['custo']}pt)",
                                font=self.fonte_hab_desc,
                                text_color="#cccccc").pack(anchor="w")

    def _conteudo_secao_feiticos(self, parent):
        from utils.feiticos import versoes_disponiveis

        if not self.feiticos_escolhidos:
            ctk.CTkLabel(parent, text="Nenhum feitiço escolhido.",
                        text_color="gray").pack()
            return

        feiticos_por_id = {f["id"]: f for f in self.feiticos_data}
        for fid in self.feiticos_escolhidos:
            feitico = feiticos_por_id.get(fid)
            if not feitico:
                continue

            linha = ctk.CTkFrame(parent, fg_color="transparent")
            linha.pack(fill="x", pady=2)

            ctk.CTkLabel(linha, text=f"• {feitico['nome']}",
                        font=self.fonte_hab_titulo).pack(side="left")
            ctk.CTkLabel(linha, text=f"  [{feitico['classe']}]",
                        font=ctk.CTkFont(size=11),
                        text_color="#aaaaaa").pack(side="left")

            versoes = versoes_disponiveis(feitico, self.grau_selecionado)
            if versoes:
                ctk.CTkLabel(parent,
                            text=f"  Versões desbloqueadas: {', '.join(versoes)}",
                            font=ctk.CTkFont(size=11),
                            text_color="#FFD700").pack(anchor="w", padx=12)

    def _tabela_info(self, parent, dados: list):
        """Renderiza uma lista de (chave, valor) em formato de tabela simples."""
        for chave, valor in dados:
            linha = ctk.CTkFrame(parent, fg_color="transparent")
            linha.pack(fill="x", pady=1)
            ctk.CTkLabel(linha, text=chave,
                        font=ctk.CTkFont(size=13), text_color="#aaaaaa",
                        width=200, anchor="w").pack(side="left")
            ctk.CTkLabel(linha, text=valor,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        anchor="w").pack(side="left")

    # ── Salvamento ────────────────────────────────────────────────────────────────

    def _salvar_ficha(self):
        import datetime

        self.nome_personagem = self.entrada_nome.get().strip()
        if not self.nome_personagem:
            self.entrada_nome.configure(border_color="#e74c3c")
            return
        self.entrada_nome.configure(border_color=("gray65", "gray35"))

        ficha = {
            "nome":             self.nome_personagem,
            "criado_em":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "classe":           self.classe_selecionada["nome"] if self.classe_selecionada else None,
            "trilha":           self.trilha_selecionada,
            "nex":              self.nex_selecionado,
            "lp":               self.lp_selecionado,
            "grau":             self.grau_selecionado,
            "totais_nex":       self.totais_nex,
            "atributos":        {s: d["valor"] for s, d in self.atributos.items()},
            "nos_comprados":    {aba: list(nos)
                                for aba, nos in self.nos_comprados.items()},
            "pontos_skilltree": self.pontos_skilltree,
            "feiticos":         self.feiticos_escolhidos,
        }

        os.makedirs("data/fichas", exist_ok=True)
        nome_arquivo = self.nome_personagem.replace(" ", "_").lower()
        caminho = f"data/fichas/{nome_arquivo}.json"

        # Evita sobrescrever fichas existentes
        contador = 1
        while os.path.exists(caminho):
            caminho = f"data/fichas/{nome_arquivo}_{contador}.json"
            contador += 1

        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(ficha, f, indent=4, ensure_ascii=False)

        self._popup_sucesso(caminho)

    def _popup_sucesso(self, caminho):
        popup = ctk.CTkToplevel(self.app)
        popup.title("Ficha salva!")
        popup.geometry("380x200")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text="✓ Ficha salva com sucesso!",
                    font=self.fonte_card_titulo,
                    text_color="#2ecc71").pack(pady=(30, 8))
        ctk.CTkLabel(popup, text=caminho,
                    font=ctk.CTkFont(size=11),
                    text_color="gray").pack(pady=(0, 20))

        ctk.CTkButton(popup, text="Criar outra ficha",
                    font=self.fonte_hab_desc,
                    command=lambda: [popup.destroy(), self._reiniciar()]).pack(pady=(0, 8))
        ctk.CTkButton(popup, text="Fechar",
                    font=self.fonte_hab_desc,
                    fg_color="transparent", border_width=1,
                    command=popup.destroy).pack()

    def _reiniciar(self):
        """Reseta o estado e volta para a tela inicial."""
        self.classe_selecionada  = None
        self.trilha_selecionada  = None
        self.nex_selecionado     = None
        self.lp_selecionado      = None
        self.totais_nex          = None
        self.grau_selecionado    = None
        self.pontos_extras_grau  = 0
        self.habilidades_trilha  = []
        self.atributos           = None
        self.pontos_disponiveis  = 0
        self.nos_comprados       = {}
        self.pontos_skilltree    = {}
        self.abas_confirmadas    = set()
        self.feiticos_escolhidos = []
        self.pontos_feiticos     = 0
        self.nome_personagem     = ""
        self._secoes_expandidas  = {}
        self._mostrar_classes()

    # ══════════════════════════════════════════════════════════════════════════
    # Navegação global
    # ══════════════════════════════════════════════════════════════════════════

    def _voltar_para_main(self):
        if self.on_voltar_para_main:
            self.on_voltar_para_main()
        self.app.destroy()