﻿using ParentopticonClientWindows;
using System;
using System.ComponentModel;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new ParentopticonMainForm());
    }
}