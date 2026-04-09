import customtkinter as ctk

class PainelAnotacoes(ctk.CTkFrame):
    """Aba: texto livre para anotações de sessão com autosave por debounce."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha          = ficha
        self._on_save        = on_save
        self._timer_autosave = None
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Anotações de sessão",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        self._texto = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13),
                                     fg_color="#1e1e1e", corner_radius=8,
                                     border_width=1, border_color="#333333")
        self._texto.pack(fill="both", expand=True)
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))
        self._texto.bind("<KeyRelease>", self._ao_digitar)

    def _ao_digitar(self, _event=None):
        if self._timer_autosave:
            self.after_cancel(self._timer_autosave)
        self._timer_autosave = self.after(1500, self._salvar)

    def _salvar(self):
        self._ficha["anotacoes"] = self._texto.get("1.0", "end-1c")
        if self._on_save:
            self._on_save()

    def atualizar(self):
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))