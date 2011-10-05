from psychopy import gui

myDlg = gui.Dlg(title="JWP's experiment")
myDlg.addText('Subject info')
myDlg.addField('Name:')
myDlg.addField('Age:', 21)
myDlg.addText('Experiment Info')
myDlg.addField('Grating Ori:',45)
myDlg.show()#show dialog and wait for OK or Cancel
if gui.OK:#then the user pressed OK
    thisInfo = myDlg.data
    print thisInfo
else: print 'user cancelled'
