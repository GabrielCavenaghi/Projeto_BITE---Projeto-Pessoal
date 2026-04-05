import customtkinter as ctk
from gerenciadorFichas import GerenciadorFichas
from criarFichas import CriadorFichas

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("Projeto BITE")
app.geometry("500x350")

def abrir_gerenciador():
    app.destroy()  # fecha a tela atual
    GerenciadorFichas()  # abre o gerenciador de fichas

def abrir_criador():
    app.destroy()
    def voltar_ao_main():
        import subprocess
        import sys
        subprocess.Popen([sys.executable, "main.py"])
        sys.exit()
    CriadorFichas(on_voltar_para_main=voltar_ao_main)


# ── Tela inicial ─────────────────────────────────────────
ctk.CTkLabel(app, text="B.I.T.E", font=ctk.CTkFont(size=48, weight="bold")).pack(pady=(60, 5))
ctk.CTkLabel(app, text="Sistema de Fichas de RPG", text_color="gray").pack(pady=(0, 50))

ctk.CTkButton(app, text="Gerenciar Fichas", width=220, height=45,
              command=abrir_gerenciador).pack(pady=8)

ctk.CTkButton(app, text="Criar Nova Ficha", width=220, height=45,
              fg_color="transparent", border_width=2,
              command=abrir_criador).pack(pady=8)

app.mainloop()