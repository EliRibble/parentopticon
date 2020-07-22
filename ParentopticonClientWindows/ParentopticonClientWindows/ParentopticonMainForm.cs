using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ParentopticonClientWindows
{
    public partial class ParentopticonMainForm : Form
    {
        public ParentopticonMainForm()
        {
            InitializeComponent();

        }

        private async void ParentopticonMainForm_Load(object sender, EventArgs e)
        {
            await this.PopulateUI();
            Debug.WriteLine("Load complete");
            this.labelLoading.Text = "Done.";
        }

        private void settingsToolStripMenuItem_Click(object sender, EventArgs e)
        {
            
        }

        private async Task PopulateUI()
        {
            Debug.WriteLine("Populating UI");
            await Task.Delay(3000);
            Debug.WriteLine("Done populating");
        }
    }
}
