using System;
using System.Drawing;
using System.Windows.Forms;

namespace Calculadora_de_Passos_de_Dano
{
    public class MensagemComCopiar : Form
    {
        private Label lblMensagem;
        private Button btnOk;
        private Button btnCopiar;

        public MensagemComCopiar(string mensagem)
        {
            // ======== Configuração do Form ========
            this.Text = "Resultado";
            this.Size = new Size(400, 180);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            // ======== Label com a mensagem ========
            lblMensagem = new Label();
            lblMensagem.Text = mensagem;
            lblMensagem.AutoSize = false;
            lblMensagem.TextAlign = ContentAlignment.MiddleCenter;
            lblMensagem.Dock = DockStyle.Top;
            lblMensagem.Height = 60;
            lblMensagem.Font = new Font("Segoe UI", 11, FontStyle.Regular);

            // ======== Botão OK ========
            btnOk = new Button();
            btnOk.Text = "OK";
            btnOk.Width = 100;
            btnOk.Height = 35;
            btnOk.Left = 60;
            btnOk.Top = 80;
            btnOk.Click += (s, e) => this.Close();

            // ======== Botão Copiar ========
            btnCopiar = new Button();
            btnCopiar.Text = "Copiar";
            btnCopiar.Width = 100;
            btnCopiar.Height = 35;
            btnCopiar.Left = 220;
            btnCopiar.Top = 80;
            btnCopiar.Click += (s, e) =>
            {
                Clipboard.SetText(A.B.mensagem);
            };

            // ======== Adiciona controles ========
            this.Controls.Add(lblMensagem);
            this.Controls.Add(btnOk);
            this.Controls.Add(btnCopiar);
        }

        // Método estático para abrir facilmente
        public static void Mostrar(string mensagem)
        {
            using (var form = new MensagemComCopiar(mensagem))
            {
                form.ShowDialog();
            }
        }
    }
}
