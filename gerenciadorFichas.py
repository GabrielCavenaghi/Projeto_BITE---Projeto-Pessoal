import customtkinter as ctk

class GerenciadorFichas:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Projeto BITE - Gerenciador de Fichas")
        self.app.geometry("900x600")

        self._criar_sidebar()
        self._criar_frames()
        mostrar_aba = self.mostrar_aba  # atalho local

        # Mostra aba inicial
        self.mostrar_aba(self.frame_atributos)

        self.app.mainloop()

    def _criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.app, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(sidebar, text="BITE", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 5))
        ctk.CTkLabel(sidebar, text="Sistema de Fichas", text_color="gray").pack(pady=(0, 30))

        abas = [
            ("Atributos",   lambda: self.mostrar_aba(self.frame_atributos)),
            ("Feitiços",    lambda: self.mostrar_aba(self.frame_feiticos)),
            ("Habilidades", lambda: self.mostrar_aba(self.frame_habilidades)),
            ("Inventário",  lambda: self.mostrar_aba(self.frame_inventario)),
            ("Anotações",   lambda: self.mostrar_aba(self.frame_anotacoes)),
        ]
        for texto, comando in abas:
            ctk.CTkButton(sidebar, text=texto, command=comando).pack(pady=5, padx=20, fill="x")

    def _criar_frames(self):
        main = ctk.CTkFrame(self.app, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.frame_atributos   = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_feiticos    = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_habilidades = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_inventario  = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_anotacoes   = ctk.CTkFrame(main, fg_color="transparent")

        # Placeholders — substitui pelo conteúdo real de cada aba
        ctk.CTkLabel(self.frame_atributos,   text="Atributos",   font=ctk.CTkFont(size=20)).pack(pady=40)
        ctk.CTkLabel(self.frame_feiticos,    text="Feitiços",    font=ctk.CTkFont(size=20)).pack(pady=40)
        ctk.CTkLabel(self.frame_habilidades, text="Habilidades", font=ctk.CTkFont(size=20)).pack(pady=40)
        ctk.CTkLabel(self.frame_inventario,  text="Inventário",  font=ctk.CTkFont(size=20)).pack(pady=40)
        ctk.CTkLabel(self.frame_anotacoes,   text="Anotações",   font=ctk.CTkFont(size=20)).pack(pady=40)

    def mostrar_aba(self, frame):
        for f in [self.frame_atributos, self.frame_feiticos,
                  self.frame_habilidades, self.frame_inventario, self.frame_anotacoes]:
            f.pack_forget()
        frame.pack(fill="both", expand=True)