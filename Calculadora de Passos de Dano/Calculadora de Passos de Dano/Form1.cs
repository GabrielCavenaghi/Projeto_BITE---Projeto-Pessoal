using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Calculadora_de_Passos_de_Dano
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        void funfa(int d, int p, int t)
        {
            int m = 1;
            while (t < 8)
            {
                p--;
                t = t + 2;
            }
            while (p != 0)
            {
                if (t == 100)
                {
                    d = d * 15;
                    t = 12;
                    p--;
                }
                else if (t == 20)
                {
                    d = d * 3;
                    t = 12;
                    p--;
                }
                else if (t == 12)
                {
                    d = d * 2;
                    t = 8;
                    p--;
                }
                else
                {
                    t = t + 2;
                    p--;
                }
                while (d > 999)
                {
                    d = d / 2;
                    m = m * 2;
                }
                A.B.m = m;
                A.B.d = d;
                A.B.t = t;
            }
        }
   
        private void label1_Click(object sender, EventArgs e)
        {

        }

        private void label3_Click(object sender, EventArgs e)
        {
            MessageBox.Show("AGORA COM TODOS OS TIPOS DE DADOS INCLUSOS");
        }

        private void numericUpDown1_ValueChanged(object sender, EventArgs e)
        {

        }
        private void button1_Click(object sender, EventArgs e)
        {
            A.B.d = Convert.ToInt32(textBox1.Text);
            A.B.p = Convert.ToInt32(numericUpDown1.Value);
            A.B.t = 0;  
            
            if(radioButton1.Checked == true)
            {
                A.B.t = 4;
            }
            if (radioButton2.Checked == true)
            {
                A.B.t = 6;
            }
            if (radioButton3.Checked == true)
            {
                A.B.t = 8;
            }
            if (radioButton4.Checked == true)
            {
                A.B.t = 10;
            }
            if (radioButton5.Checked == true)
            {
                A.B.t = 12;
            }
            if (radioButton6.Checked == true)
            {
                A.B.t = 20;
            }
            if (radioButton7.Checked == true)
            {
                A.B.t = 100;
            }
            funfa(A.B.d, A.B.p, A.B.t);    
            A.B.mensagem = "(" + A.B.d + "d" + A.B.t + ")*" + A.B.m;
            MensagemComCopiar.Mostrar("O Dado principal é: " + A.B.mensagem);

        }

        private void textBox1_TextChanged(object sender, EventArgs e)
        {

        }

        private void label2_Click(object sender, EventArgs e)
        {

        }
    }
}
