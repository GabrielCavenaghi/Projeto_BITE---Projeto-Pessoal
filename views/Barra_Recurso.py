import customtkinter as ctk

class BarraRecurso(ctk.CTkFrame):
    """
    Barra de recurso reutilizável.
    Layout: label + fração  |  barra de progresso  |  [−] [entrada] [+]  [máx]
    on_change(novo_atual) é chamado após cada alteração.
    Suporta valores temporários (atual pode exceder máximo).
    """

    def __init__(self, parent, label: str, atual: int, maximo: int,
                 cor_barra: str, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._atual     = atual
        self._maximo    = maximo
        self._on_change = on_change

        # Linha superior: nome + fracção
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        ctk.CTkLabel(topo, text=label,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cccccc").pack(side="left")

        self._lbl_fracao = ctk.CTkLabel(topo, text=self._texto_fracao(),
                                        font=ctk.CTkFont(size=12),
                                        text_color="#888888")
        self._lbl_fracao.pack(side="right")

        # Barra visual
        self._barra = ctk.CTkProgressBar(self, height=8, corner_radius=4,
                                         progress_color=cor_barra,
                                         fg_color="#2a2a2a")
        self._barra.pack(fill="x", pady=(4, 6))
        self._atualizar_barra()

        # Controles: − | entrada | + | máx
        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.pack(fill="x")

        ctk.CTkButton(controles, text="−", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._decrementar).pack(side="left")

        self._entrada = ctk.CTkEntry(controles, width=70, height=30,
                                     justify="center",
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self._entrada.insert(0, str(self._atual))
        self._entrada.pack(side="left", padx=6)
        self._entrada.bind("<Return>",   self._ao_confirmar_entrada)
        self._entrada.bind("<FocusOut>", self._ao_confirmar_entrada)

        ctk.CTkButton(controles, text="+", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._incrementar).pack(side="left")

        ctk.CTkButton(controles, text="máx", width=46, height=30,
                      font=ctk.CTkFont(size=11),
                      fg_color="transparent", border_width=1,
                      border_color="#444444", text_color="#888888",
                      command=self._editar_maximo).pack(side="right")

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _texto_fracao(self) -> str:
        return f"{self._atual} / {self._maximo}"

    def _atualizar_barra(self):
        if self._maximo > 0:
            # A barra fica cheia (1.0) se atual >= máximo, senão proporcional
            prog = min(1.0, self._atual / self._maximo)
        else:
            prog = 0.0
        self._barra.set(prog)

    def _atualizar_ui(self):
        if not self.winfo_exists():
            return
        self._lbl_fracao.configure(text=self._texto_fracao())
        self._atualizar_barra()
        self._entrada.delete(0, "end")
        self._entrada.insert(0, str(self._atual))
        if self._on_change:
            self._on_change(self._atual)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _decrementar(self):
        self._atual = max(0, self._atual - 1)
        self._atualizar_ui()

    def _incrementar(self):
        # Permite ultrapassar o máximo (recursos temporários)
        self._atual += 1
        self._atualizar_ui()

    def _ao_confirmar_entrada(self, _event=None):
        try:
            valor = int(self._entrada.get())
            # Apenas não permite negativo
            self._atual = max(0, valor)
        except ValueError:
            pass
        self._atualizar_ui()

    def _editar_maximo(self):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Editar máximo")
        popup.geometry("280x150")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text="Novo valor máximo:",
                     font=ctk.CTkFont(size=13)).pack(pady=(20, 6))

        entrada = ctk.CTkEntry(popup, width=100, justify="center",
                               font=ctk.CTkFont(size=14))
        entrada.insert(0, str(self._maximo))
        entrada.pack()
        entrada.focus()

        def confirmar():
            try:
                novo = int(entrada.get())
                if novo >= 0:
                    self._maximo = novo
                    # Não reduz o atual (mantém temporários)
                    self._atualizar_ui()
            except ValueError:
                pass
            popup.destroy()

        entrada.bind("<Return>", lambda _: confirmar())
        ctk.CTkButton(popup, text="Confirmar", command=confirmar).pack(pady=12)

    # ── API pública ───────────────────────────────────────────────────────────

    def get_atual(self) -> int:
        return self._atual

    def get_maximo(self) -> int:
        return self._maximo

    def set_valores(self, atual: int, maximo: int):
        self._atual  = atual
        self._maximo = maximo
        self._atualizar_ui()