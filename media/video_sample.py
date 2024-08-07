from psychopy import visual, core  # import some libraries from PsychoPy

#create a window
mywin = visual.Window([800, 600], color=[-1.0, -1.0, -1.0], monitor="testMonitor", units="deg")

#create some stimuli
smily = visual.ImageStim(win=mywin, image='./images/smiley_transparent.png')
#fixation = visual.GratingStim(win=mywin, size=0.5, pos=[0,0], sf=0, rgb=-1)

#draw the stimuli and update the window
smily.draw()
#fixation.draw()
mywin.update()

#pause, so you get a chance to see it!
core.wait(5.0)