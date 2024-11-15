from psychopy import visual, core  # import some libraries from PsychoPy

BACKGROUND_COLOR = [-1, -1, -1] # 0, 0, 0

#create a window
#mywin = visual.Window([800, 600], color=[-1.0, -1.0, -1.0], monitor="testMonitor", units="deg")
#mywin = visual.Window([800, 600], color=[-1.0, -1.0, -1.0])

fullscreen_mode = False
display_size = [800, 600]
window_position = [100, 100]

win = visual.Window(display_size, color=BACKGROUND_COLOR, fullscr=fullscreen_mode, pos=window_position)

#create some stimuli
#smily = visual.ImageStim(win=mywin, image='./images/smiley_transparent.png')
#fixation = visual.GratingStim(win=mywin, size=0.5, pos=[0,0], sf=0, rgb=-1)

#draw the stimuli and update the window
#smily.draw()
#fixation.draw()
win.update()

#pause, so you get a chance to see it!
core.wait(5.0)