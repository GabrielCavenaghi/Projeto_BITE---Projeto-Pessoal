import customtkinter as ctk
from gerenciadorFichas import GerenciadorFichas
from criarFichas import CriadorFichas

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

import tkinter as tk

def report_callback_exception(exc, val, tb, *args):   # Aceita 4 argumentos
    import traceback
    print("--- Tkinter Exception ---")
    traceback.print_exception(exc, val, tb)
    print("-------------------------")

tk.Tk.report_callback_exception = report_callback_exception

class MainApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Projeto BITE")
        self.app.geometry("500x350")
        
        self._criar_tela_inicial()
        self.app.mainloop()
    
    def _criar_tela_inicial(self):
        """Cria a tela inicial do menu principal"""
        # Limpa a janela atual
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Título
        ctk.CTkLabel(self.app, text="B.I.T.E", 
                     font=ctk.CTkFont(size=48, weight="bold")).pack(pady=(60, 5))
        ctk.CTkLabel(self.app, text="Sistema de Fichas de RPG", 
                     text_color="gray").pack(pady=(0, 50))
        
        # Botões
        ctk.CTkButton(self.app, text="Gerenciar Fichas", width=220, height=45,
                      command=self.abrir_gerenciador).pack(pady=8)
        
        ctk.CTkButton(self.app, text="Criar Nova Ficha", width=220, height=45,
                      fg_color="transparent", border_width=2,
                      command=self.abrir_criador).pack(pady=8)
    
    def abrir_gerenciador(self):
        self.app.withdraw()
        def voltar_ao_main():
            self.app.deiconify()
        # ↓↓↓ adicione o argumento parent ↓↓↓
        gerenciador = GerenciadorFichas(parent=self.app, on_voltar_para_main=voltar_ao_main)
    
    def abrir_criador(self):
        """Abre o criador de fichas"""
        self.app.withdraw()
        
        def voltar_ao_main():
            self.app.deiconify()
        
        criador = CriadorFichas(on_voltar_para_main=voltar_ao_main)

# Inicia o aplicativo
if __name__ == "__main__":
    app = MainApp()